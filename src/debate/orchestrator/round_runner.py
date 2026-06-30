"""Round execution and process-management helpers for the orchestrator."""

from __future__ import annotations

import multiprocessing
from typing import TYPE_CHECKING

from debate.models.messages import DebateMessage, Verdict
from debate.orchestrator.agent_workers import run_con_worker, run_father_worker, run_pro_worker
from debate.shared.config import ConfigManager

if TYPE_CHECKING:
    from debate.orchestrator.watchdog import Watchdog


def run_round_via_processes(
    rnd: int,
    prev_con: DebateMessage | None,
    config: ConfigManager,
    pro_tq: multiprocessing.Queue,
    pro_rq: multiprocessing.Queue,
    con_tq: multiprocessing.Queue,
    con_rq: multiprocessing.Queue,
    fth_tq: multiprocessing.Queue,
    fth_rq: multiprocessing.Queue,
) -> tuple[DebateMessage, DebateMessage]:
    """Run one round using the real agent processes."""
    timeout = config.llm_timeout
    route_timeout = config.round_timeout

    pro_tq.put({"round": rnd, "prev": prev_con.to_json() if prev_con else None})
    pro_resp = pro_rq.get(timeout=timeout)
    if not pro_resp["ok"]:
        raise RuntimeError(f"Pro agent error: {pro_resp['error']}")
    pro_msg = DebateMessage.from_json(pro_resp["data"])

    fth_tq.put({"type": "route", "message": pro_msg.to_json(), "dest": "con"})
    fth_rq.get(timeout=route_timeout)

    con_tq.put({"round": rnd, "pro_msg": pro_msg.to_json()})
    con_resp = con_rq.get(timeout=timeout)
    if not con_resp["ok"]:
        raise RuntimeError(f"Con agent error: {con_resp['error']}")
    con_msg = DebateMessage.from_json(con_resp["data"])

    fth_tq.put({"type": "route", "message": con_msg.to_json(), "dest": "pro"})
    fth_rq.get(timeout=route_timeout)

    return pro_msg, con_msg


def get_verdict_via_process(
    transcript: list[DebateMessage],
    fth_tq: multiprocessing.Queue,
    fth_rq: multiprocessing.Queue,
) -> Verdict:
    """Ask the Father process to evaluate the transcript and return a Verdict."""
    fth_tq.put({
        "type": "evaluate",
        "transcript": [m.to_json() for m in transcript],
    })
    resp = fth_rq.get(timeout=120)
    if not resp["ok"]:
        raise RuntimeError(f"Father evaluation error: {resp['error']}")
    return Verdict.from_json(resp["verdict"])


def start_agent_processes(
    config_dir: str,
    pro_tq: multiprocessing.Queue,
    pro_rq: multiprocessing.Queue,
    con_tq: multiprocessing.Queue,
    con_rq: multiprocessing.Queue,
    fth_tq: multiprocessing.Queue,
    fth_rq: multiprocessing.Queue,
) -> dict:
    """Spawn all three agent processes and return the procs dict."""
    procs = {
        "pro": multiprocessing.Process(
            target=run_pro_worker, args=(config_dir, pro_tq, pro_rq), daemon=False
        ),
        "con": multiprocessing.Process(
            target=run_con_worker, args=(config_dir, con_tq, con_rq), daemon=False
        ),
        "father": multiprocessing.Process(
            target=run_father_worker, args=(config_dir, fth_tq, fth_rq), daemon=False
        ),
    }
    for p in procs.values():
        p.start()
    return procs


def register_agents_with_watchdog(
    watchdog: Watchdog,
    config_dir: str,
    pro_role: object,
    con_role: object,
    father_role: object,
    procs: dict,
    queues: tuple,
) -> None:
    """Register all three agent processes with the Watchdog and start monitoring."""
    pro_tq, pro_rq, con_tq, con_rq, fth_tq, fth_rq = queues
    watchdog.register(
        pro_role, procs["pro"],
        lambda: multiprocessing.Process(target=run_pro_worker, args=(config_dir, pro_tq, pro_rq)),
    )
    watchdog.register(
        con_role, procs["con"],
        lambda: multiprocessing.Process(target=run_con_worker, args=(config_dir, con_tq, con_rq)),
    )
    watchdog.register(
        father_role, procs["father"],
        lambda: multiprocessing.Process(
            target=run_father_worker, args=(config_dir, fth_tq, fth_rq)
        ),
    )
    watchdog.start()
