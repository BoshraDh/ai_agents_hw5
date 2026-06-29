"""Round execution helpers — extracted to keep debate_orchestrator.py under 150 lines."""

from __future__ import annotations

import multiprocessing

from debate.models.messages import DebateMessage, Verdict
from debate.shared.config import ConfigManager


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
