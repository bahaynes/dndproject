import asyncio
import json
import logging
from typing import List, Set

logger = logging.getLogger(__name__)

class EventService:
    def __init__(self):
        self.subscribers: Set[asyncio.Queue] = set()

    async def subscribe(self):
        queue = asyncio.Queue()
        self.subscribers.add(queue)
        logger.info(f"New subscriber. Total: {len(self.subscribers)}")
        try:
            while True:
                message = await queue.get()
                yield message
        except asyncio.CancelledError:
            logger.info("Subscriber disconnected")
        finally:
            self.subscribers.remove(queue)
            logger.info(f"Subscriber removed. Total: {len(self.subscribers)}")

    async def broadcast(self, event: str, data: dict = None):
        if data is None:
            data = {}
        # SSE format
        message = f"event: {event}\ndata: {json.dumps(data)}\n\n"

        # We need to copy the set to avoid modification during iteration if a client disconnects simultaneously
        # (though async shouldn't have race conditions in single thread, it's safer)
        for queue in list(self.subscribers):
            await queue.put(message)

event_service = EventService()
