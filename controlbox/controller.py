import logging
from binascii import unhexlify

from .protocol.decoder import ResponseDecoder
from .protocol.v1 import ProtocolV1

from .resolver import (
    RequestResponseResolver,
    RequestResponseMatcher
)

from .conduit.serial import SerialConduit

import codecs

LOGGER = logging.getLogger(__name__)

class ControlboxCommandMatcher(RequestResponseMatcher):
    """
    Matches a Response with an awaiting Request
    """
    def match(self, obj1, obj2):
        return (obj1.opcode == obj2.opcode)


class SimpleVirtualController:
    def transmit_bytes(self, data: bytes):
        command = CBoxCommand.parse(data)
        return self.process_command_request(command)

    def process_command_request(self, aCommandRequest, data):
        if command.opcode == CBoxOpcodeEnum.encmapping['LIST_OBJECTS']:
            command_request = ListObjectsCommandRequest.parse(data)
            profile_id = command_request.profile_id
            return ListObjectsCommandResponse.build({'id': profile_id})

        return None



class Controller:
    """
    A Controller represents a physical device that implements a protocol
    and communicates using a Conduit (e.g. TCP/IP, Serial port, ...).
    """
    def __init__(self, aConduit, aProtocol=ProtocolV1()):
        self.conduit = aConduit
        self.resolver = RequestResponseResolver(ControlboxCommandMatcher)
        self.protocol = aProtocol

    def connect(self):
        if not self.is_connected:
            self.conduit.bind()

    async def process_messages(self):
        """
        Processes all message coming from the protocol
        """
        async for raw_msg in self.conduit.watch_messages():
            response_command = self.protocol.response_command_from_bytes(unhexlify(raw_msg))
            self.resolver.match_response(response_command)

    async def send(self, aCommand):
        if not self.is_connected:
            raise NotConnectedError

        bytes_to_send = codecs.encode(aCommand, "hex")

        # Add this command to resolver to make sure we catch reply if the
        # controller is quick to respond
        future = self.resolver.queue_request(aCommand)

        # Send the bytes on wire
        await self.conduit.write(bytes_to_send)
        await self.conduit.write(b"\n")

        return future

    @property
    def is_connected(self):
        return self.conduit.is_bound

