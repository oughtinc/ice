import asyncio


class PeekableQueue(asyncio.PriorityQueue):
    async def peek(self):
        priority, head = await self.get()
        await self.put((priority, head))
        return head

    def peek_nowait(self):
        priority, head = self.get_nowait()
        self.put_nowait((priority, head))
        return head
