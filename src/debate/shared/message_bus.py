"""MessageBus — multiprocessing.Queue wrapper for typed JSON IPC."""

from __future__ import annotations

import multiprocessing
import queue

from debate.models.messages import DebateMessage


class MessageBus:
    """Wraps a pair of multiprocessing Queues for bidirectional agent IPC."""

    def __init__(self) -> None:
        self._to_father: multiprocessing.Queue = multiprocessing.Queue()
        self._to_pro: multiprocessing.Queue = multiprocessing.Queue()
        self._to_con: multiprocessing.Queue = multiprocessing.Queue()

    def send_to_father(self, message: DebateMessage) -> None:
        """Put a JSON-serialized message onto the Father's inbound queue."""
        self._to_father.put(message.to_json())

    def send_to_pro(self, message: DebateMessage) -> None:
        """Put a JSON-serialized message onto the Pro agent's inbound queue."""
        self._to_pro.put(message.to_json())

    def send_to_con(self, message: DebateMessage) -> None:
        """Put a JSON-serialized message onto the Con agent's inbound queue."""
        self._to_con.put(message.to_json())

    def receive_from_father(self, timeout: float = 60.0) -> DebateMessage:
        """Block until a message arrives on the Father's outbound queue."""
        try:
            raw = self._to_father.get(timeout=timeout)
            return DebateMessage.from_json(raw)
        except queue.Empty as exc:
            raise TimeoutError("Timeout waiting for Father message") from exc

    def receive_for_pro(self, timeout: float = 60.0) -> DebateMessage:
        """Block until a message arrives on the Pro agent's inbound queue."""
        try:
            raw = self._to_pro.get(timeout=timeout)
            return DebateMessage.from_json(raw)
        except queue.Empty as exc:
            raise TimeoutError("Timeout waiting for Pro message") from exc

    def receive_for_con(self, timeout: float = 60.0) -> DebateMessage:
        """Block until a message arrives on the Con agent's inbound queue."""
        try:
            raw = self._to_con.get(timeout=timeout)
            return DebateMessage.from_json(raw)
        except queue.Empty as exc:
            raise TimeoutError("Timeout waiting for Con message") from exc
