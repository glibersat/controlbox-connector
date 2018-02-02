import asyncio

class VirtualControllerConduit:
    """
    A Conduit for a testing purpose
    """
    def __init__(self, aVirtualController):
        self._loop = asyncio.get_event_loop()
        self.controller = aVirtualController

        self._is_bound = False

    def bind(self):
        self._is_bound = True

    async def write(self, data):
        self.controller.transmit_bytes(data)

    async def watch_messages(self):
        yield await self.protocol.watch_messages()

    @property
    def is_bound(self):
        return self._is_bound
