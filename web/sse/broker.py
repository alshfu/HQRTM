"""In-process pub/sub-broker för SSE.

Varje SSE-klient prenumererar på händelser för sitt user_id (kö). En bakgrunds-watcher
för Change Stream publicerar matchningar. Brokern lever i minnet i web-processen — vid flera
web-processer behövs en gemensam backend (Redis pub/sub) eller att varje process prenumererar
på sin egen Change Stream (planeras vid skalning, Fas 8/10).
"""

from __future__ import annotations

import queue
import threading

_MAX_QUEUE = 100


class Broker:
    def __init__(self) -> None:
        self._subs: dict[str, set[queue.Queue]] = {}
        self._lock = threading.Lock()

    def subscribe(self, user_id: str) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=_MAX_QUEUE)
        with self._lock:
            self._subs.setdefault(user_id, set()).add(q)
        return q

    def unsubscribe(self, user_id: str, q: queue.Queue) -> None:
        with self._lock:
            subs = self._subs.get(user_id)
            if subs:
                subs.discard(q)
                if not subs:
                    self._subs.pop(user_id, None)

    def publish(self, user_id: str, data: dict) -> int:
        """Leverera händelsen till alla prenumeranter för user_id. Returnerar antal leveranser."""
        delivered = 0
        with self._lock:
            targets = list(self._subs.get(user_id, ()))
        for q in targets:
            try:
                q.put_nowait(data)
                delivered += 1
            except queue.Full:
                pass  # långsam klient — hoppas över (hämtas vid nästa polling)
        return delivered

    def subscriber_count(self, user_id: str) -> int:
        with self._lock:
            return len(self._subs.get(user_id, ()))


# gemensam broker för processen
broker = Broker()
