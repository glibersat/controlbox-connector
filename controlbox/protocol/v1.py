from .abstract import ControlboxProtocol

from .decoder import ResponseDecoder

from .commands import (
    CBoxOpcodeEnum,
    ReadValueCommandRequest,
    ReadValueCommandResponse
)

class ProtocolV1(ControlboxProtocol):
    """
    First protocol version, mostly as described by Matt in:
    https://github.com/ctlbox/controlbox-cpp/blob/develop/docs/controlbox.rst
    """
    decoder = ResponseDecoder()

    command_mapping = {
        CBoxOpcodeEnum.encmapping['READ_VALUE']: (ReadValueCommandRequest, ReadValueCommandResponse)
    }

    def command_response_from_bytes(self, data : bytes):
        """
        Return a CommandResponse, decoded from a byte array
        """
        return self.decoder.from_bytes(data)
