import logging

LOGGER = logging.getLogger(__name__)

from .commands import (
    CBoxCommand,
    ReadValueCommandResponse,
    CreateObjectCommandResponse,
    ListProfilesCommandResponse,
    ListObjectsCommandResponse,
    DeleteObjectCommandResponse
)


class ResponseDecoder:
    """
    Try to decode a sequence of bytes and make objects
    """
    def from_bytes(self, msg : bytes):
        from binascii import hexlify
        LOGGER.debug("<-- {0} / {1}".format(msg, hexlify(msg)))

        res = CBoxCommand.parse(msg)

        if res.opcode == "READ_VALUE":
            print("<-- READ VALUE")
            decoded = ReadValueCommandResponse.parse(msg)
            print(decoded)
            from controlbox.protocol.protobuf.OneWireTempSensor_pb2 import OneWireTempSensor
            sens = OneWireTempSensor()
            sens.ParseFromString(decoded.data)
            LOGGER.debug("Address: 0x{0}".format(hexlify(sens.settings.address).decode()))
            LOGGER.debug("Is Connected? {0}".format(sens.state.connected))
            LOGGER.debug("Temperature: {0}".format(sens.state.value/256.0))

        elif res.opcode == "CREATE_OBJECT":
            LOGGER.debug("<-- CREATE OBJECT")
            return CreateObjectCommandResponse.parse(msg)
        elif res.opcode == "CREATE_PROFILE":
            LOGGER.debug("<-- CREATE PROFILE")
            return CreateProfileCommandResponse.parse(msg)
        elif res.opcode == "ACTIVATE_PROFILE":
            LOGGER.debug("<-- ACTIVATE PROFILE")
            return ActivateProfileCommandResponse.parse(msg)
        elif res.opcode == "LIST_OBJECTS":
            LOGGER.debug("<-- LIST OBJECTS")
            return ListObjectsCommandResponse.parse(msg)
        elif res.opcode == "DELETE_OBJECT":
            LOGGER.debug("<-- DELETE OBJECT")
            return DeleteObjectCommandResponse.parse(msg)
        elif res.opcode == "LIST_PROFILES":
            LOGGER.debug("<-- LIST PROFILES")
            return ListProfilesCommandResponse.parse(msg)

        return None
