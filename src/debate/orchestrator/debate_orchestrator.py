"""DebateOrchestrator — coordinates 3 agent processes through N debate rounds."""

from __future__ import annotations

import contextlib
import multiprocessing
import uuid
from pathlib import Path

from debate.agents.con_agent import ConAgent
from debate.agents.father_agent import FatherAgent
from debate.agents.pro_agent import ProAgent
from debate.constants import DebateStatus
from debate.models.messages import DebateMessage, Verdict
from debate.orchestrator.agent_workers import run_con_worker, run_father_worker, run_pro_worker
from debate.orchestrator.round_runner import get_verdict_via_process, run_round_via_processes
from debate.orchestrator.watchdog import Watchdog
from debate.shared.config import ConfigManager
from debate.shared.gatekeeper import ApiGatekeeper
from debate.shared.logger import DebateLogger


class DebateOrchestrator:
    """Spawns 3 agent processes, routes messages through Father, collects verdict."""

    def __init__(self, config_dir: str = "config", use_processes: bool = True) -> None:
        self._config_dir = str(Path(config_dir).resolve())
        self._config = ConfigManager(config_dir)
        self._use_processes = use_processes
        self._session_id = str(uuid.uuid4())[:8]
        self._logger = DebateLogger(self._config, self._session_id)
        self._transcript: list[DebateMessage] = []
        self._verdict: Verdict | None = None
        self._status = DebateStatus.IDLE
        _gk = ApiGatekeeper(self._config)
        self._pro = ProAgent(self._config, _gk, None)
        self._con = ConAgent(self._config, _gk, None)
        self._father = FatherAgent(self._config, _gk, None)
        self._watchdog: Watchdog | None = None
        self._pro_tq: multiprocessing.Queue = multiprocessing.Queue()
        self._pro_rq: multiprocessing.Queue = multiprocessing.Queue()
        self._con_tq: multiprocessing.Queue = multiprocessing.Queue()
        self._con_rq: multiprocessing.Queue = multiprocessing.Queue()
        self._fth_tq: multiprocessing.Queue = multiprocessing.Queue()
        self._fth_rq: multiprocessing.Queue = multiprocessing.Queue()
        self._procs: dict[str, multiprocessing.Process] = {}

    @property
    def session_id(self) -> str:
        return self._session_id

    def get_session_id(self) -> str:
        return self._session_id

    @property
    def status(self) -> DebateStatus:
        return self._status

    def run(self, topic: str | None = None) -> tuple[list[DebateMessage], Verdict]:
        """Run the full debate. Returns (transcript, verdict)."""
        if topic:
            self._config.set_topic(topic)
        self._status = DebateStatus.RUNNING
        self._logger.info("DEBATE_START", topic=self._config.topic)
        try:
            if self._use_processes:
                self._start_processes()
                self._start_watchdog()
            result = self._run_rounds()
            self._status = DebateStatus.COMPLETED
            self._logger.info("DEBATE_END", winner=result[1].winner.value)
            return result
        except Exception as exc:
            self._status = DebateStatus.FAILED
            self._logger.error("DEBATE_FAILED", error=str(exc))
            raise
        finally:
            self._logger.save_transcript([m.model_dump() for m in self._transcript])
            if self._use_processes:
                self.stop()

    def _start_processes(self) -> None:
        """GAP-1: spawn each agent as an independent multiprocessing.Process."""
        args = self._config_dir
        self._procs = {
            "pro": multiprocessing.Process(
                target=run_pro_worker, args=(args, self._pro_tq, self._pro_rq), daemon=False
            ),
            "con": multiprocessing.Process(
                target=run_con_worker, args=(args, self._con_tq, self._con_rq), daemon=False
            ),
            "father": multiprocessing.Process(
                target=run_father_worker, args=(args, self._fth_tq, self._fth_rq), daemon=False
            ),
        }
        for p in self._procs.values():
            p.start()

    def _start_watchdog(self) -> None:
        """GAP-2: create Watchdog, register all 3 processes, start monitoring."""
        self._watchdog = Watchdog(self._config, self._logger)
        self._watchdog.register(
            self._pro.role, self._procs["pro"],
            lambda: multiprocessing.Process(
                target=run_pro_worker, args=(self._config_dir, self._pro_tq, self._pro_rq)
            ),
        )
        self._watchdog.register(
            self._con.role, self._procs["con"],
            lambda: multiprocessing.Process(
                target=run_con_worker, args=(self._config_dir, self._con_tq, self._con_rq)
            ),
        )
        self._watchdog.register(
            self._father.role, self._procs["father"],
            lambda: multiprocessing.Process(
                target=run_father_worker, args=(self._config_dir, self._fth_tq, self._fth_rq)
            ),
        )
        self._watchdog.start()

    def _run_rounds(self) -> tuple[list[DebateMessage], Verdict]:
        prev_con: DebateMessage | None = None
        for rnd in range(1, self._config.max_rounds + 1):
            self._logger.info("ROUND_START", round=rnd)
            if self._watchdog:
                self._watchdog.check_for_fatal_error()
            if self._use_processes:
                pro_msg, con_msg = run_round_via_processes(
                    rnd, prev_con, self._config,
                    self._pro_tq, self._pro_rq,
                    self._con_tq, self._con_rq,
                    self._fth_tq, self._fth_rq,
                )
            else:
                pro_msg = self._pro.generate_argument(rnd, prev_con)
                con_msg = self._con.generate_counter(rnd, pro_msg)
            self._transcript += [pro_msg, con_msg]
            prev_con = con_msg
            self._logger.info("ROUND_END", round=rnd)
        verdict = (
            get_verdict_via_process(self._transcript, self._fth_tq, self._fth_rq)
            if self._use_processes
            else self._father.evaluate_debate(self._transcript)
        )
        self._verdict = verdict
        return self._transcript, verdict

    def stop(self) -> None:
        """GAP-11: gracefully stop all processes and Watchdog."""
        if self._watchdog:
            self._watchdog.stop()
        for q in (self._pro_tq, self._con_tq, self._fth_tq):
            with contextlib.suppress(Exception):
                q.put_nowait(None)
        for p in self._procs.values():
            p.join(timeout=5)
            if p.is_alive():
                p.terminate()
        self._procs.clear()

    def get_transcript(self) -> list[DebateMessage]:
        return list(self._transcript)

    def get_verdict(self) -> Verdict | None:
        return self._verdict
