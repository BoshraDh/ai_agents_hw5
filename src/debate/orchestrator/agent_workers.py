"""Module-level process entry functions for each agent.

Must be defined at module scope (not as lambdas or closures) so Python's
multiprocessing 'spawn' method (used on Windows) can pickle them.
"""

from __future__ import annotations

from multiprocessing import Queue


def run_pro_worker(config_dir: str, task_q: Queue, result_q: Queue) -> None:
    """Pro agent process: receive generate tasks, return DebateMessage JSON."""
    from debate.agents.pro_agent import ProAgent
    from debate.models.messages import DebateMessage
    from debate.shared.config import ConfigManager
    from debate.shared.gatekeeper import ApiGatekeeper

    config = ConfigManager(config_dir)
    pro = ProAgent(config, ApiGatekeeper(config), None)
    while True:
        task = task_q.get()
        if task is None:
            break
        try:
            prev = DebateMessage.from_json(task["prev"]) if task.get("prev") else None
            msg = pro.generate_argument(task["round"], prev)
            result_q.put({"ok": True, "data": msg.to_json()})
        except Exception as exc:
            result_q.put({"ok": False, "error": str(exc)})


def run_con_worker(config_dir: str, task_q: Queue, result_q: Queue) -> None:
    """Con agent process: receive generate tasks, return DebateMessage JSON."""
    from debate.agents.con_agent import ConAgent
    from debate.models.messages import DebateMessage
    from debate.shared.config import ConfigManager
    from debate.shared.gatekeeper import ApiGatekeeper

    config = ConfigManager(config_dir)
    con = ConAgent(config, ApiGatekeeper(config), None)
    while True:
        task = task_q.get()
        if task is None:
            break
        try:
            pro_msg = DebateMessage.from_json(task["pro_msg"])
            msg = con.generate_counter(task["round"], pro_msg)
            result_q.put({"ok": True, "data": msg.to_json()})
        except Exception as exc:
            result_q.put({"ok": False, "error": str(exc)})


def run_father_worker(config_dir: str, task_q: Queue, result_q: Queue) -> None:
    """Father agent process: validate/route messages and evaluate transcript."""
    from debate.agents.father_agent import FatherAgent
    from debate.models.messages import DebateMessage
    from debate.shared.config import ConfigManager
    from debate.shared.gatekeeper import ApiGatekeeper

    config = ConfigManager(config_dir)
    father = FatherAgent(config, ApiGatekeeper(config), None)
    while True:
        task = task_q.get()
        if task is None:
            break
        try:
            if task["type"] == "route":
                msg = DebateMessage.from_json(task["message"])
                father._validate_message(msg)
                result_q.put({"ok": True, "message": msg.to_json()})
            elif task["type"] == "evaluate":
                transcript = [DebateMessage.from_json(m) for m in task["transcript"]]
                verdict = father.evaluate_debate(transcript)
                result_q.put({"ok": True, "verdict": verdict.to_json()})
        except Exception as exc:
            result_q.put({"ok": False, "error": str(exc)})
