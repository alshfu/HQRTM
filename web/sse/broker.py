"""In-process pub/sub брокер для SSE.

Каждый SSE-клиент подписывается на события своего user_id (очередь). Фоновый watcher
Change Stream публикует совпадения. Брокер живёт в памяти процесса web — при нескольких
web-процессах нужен общий backend (Redis pub/sub) или подписка каждого процесса на свой
Change Stream (планируется при масштабировании, Фаза 8/10).
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
        """Доставить событие всем подписчикам user_id. Возвращает число доставок."""
        delivered = 0
        with self._lock:
            targets = list(self._subs.get(user_id, ()))
        for q in targets:
            try:
                q.put_nowait(data)
                delivered += 1
            except queue.Full:
                pass  # медленный клиент — пропускаем (получит при следующем polling)
        return delivered

    def subscriber_count(self, user_id: str) -> int:
        with self._lock:
            return len(self._subs.get(user_id, ()))


# единый брокер процесса
broker = Broker()
