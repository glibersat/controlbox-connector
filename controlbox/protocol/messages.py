import logging

from construct import *

from OneWireTempSensor_pb2 import OneWireTempSensor

LOGGER = logging.getLogger(__name__)


CBoxOpcodeEnum = Enum(Byte,
                      READ_VALUE = 1, # read a value
                      WRITE_VALUE = 2, # write a value
                      CREATE_OBJECT = 3, # add object in a container
   	                  DELETE_OBJECT = 4, # delete the object at the specified location
   	                  LIST_OBJECTS = 5,	# list objects in a container
                      FREE_SLOT = 6, # retrieves the next free slot in a container
                      CREATE_PROFILE = 7, # create a new profile
                      DELETE_PROFILE = 8, # delete a profile
                      ACTIVATE_PROFILE = 9, # activate a profile
                      LOG_VALUES = 10, # log values from the selected container
                      RESET = 11, # reset the device
                      FREE_SLOT_ROOT = 12, # find the next free slot in the root container
                      UNUSED = 13, # unused
                      LIST_PROFILES = 14, # list the define profile IDs and the active profile
                      READ_SYSTEM_VALUE = 15, # read the value of a system object
                      SET_SYSTEM_VALUE = 16, # write the value of a system object
                      SET_MASK_VALUE = 17
)

BrewBloxObjectTypeEnum = Enum(Byte,
                              TEMPERATURE_SENSOR = 6
)

CBoxCommand = Struct(
    "opcode" / CBoxOpcodeEnum,
)

# CREATE OBJECT
CreateObjectCommandRequest = Struct(
    "opcode" / Const(0x03, Byte),
    "id" / VariableLengthIDAdapter(),
    "type" / BrewBloxObjectTypeEnum,
    "data" / PrefixedArray(VarInt, Byte),
)

CreateObjectCommandResponse = Struct(
    "opcode" / Const(0x03, Byte),
    "id" / VariableLengthIDAdapter(),
    "type" / Optional(BrewBloxObjectTypeEnum),
    "data" / Optional(PrefixedArray(VarInt, Byte)),
    "status" / Int8sb,
    Terminated
)

# CREATE PROFILE
CreateProfileCommandRequest = Struct(
    "opcode" / Const(0x07, Byte),
)

CreateProfileCommandResponse = Struct(
    "opcode" / Const(0x07, Byte),
    "profile_id" / Int8sb,
    Terminated
)

# ACTIVATE PROFILE
ActivateProfileCommandRequest = Struct(
    "opcode" / Const(0x09, Byte),
    "profile_id" / Int8sb
)

ActivateProfileCommandResponse = Struct(
    "opcode" / Const(0x09, Byte),
    "profile_id" / Int8sb,
    "status" / Int8sb,
    Terminated
)

# LIST PROFILES
ListProfilesCommandRequest = Struct(
    "opcode" / Const(0x0E, Byte),
)

ListProfilesCommandResponse = Struct(
    "opcode" / Const(0x0E, Byte),
    "active_profile" / Int8ub
#    "defined_profiles" / Sequence(Int8ub)
)


# LIST PROFILE OBJECTS
ListObjectsCommandRequest = Struct(
    "opcode" / Const(0x05, Byte),
    "profile_id" / Int8sb
)

ListObjectsCommandResponse = Struct(
    "opcode" / Const(0x05, Byte),
    "profile_id" / Int8sb,
    "status" / Int8sb,
    Padding(1), # FIXME Protocol error
    "objects" / Optional(Sequence(CreateObjectCommandRequest)),
    "terminator" / Const(0x00, Byte),
    Terminated
)

# READ VALUE
ReadValueCommandRequest = Struct(
    "opcode" / Const(0x01, Byte),
    "id" / VariableLengthIDAdapter(),
    "type" / BrewBloxObjectTypeEnum,
    "size" / Default(Int8ub, 0)
)

ReadValueCommandResponse = Struct(
    "opcode" / Const(0x01, Byte),
    "id" / VariableLengthIDAdapter(),
    "type" / BrewBloxObjectTypeEnum,
    "expectedsize" / Int8sb,
    "real-type" / BrewBloxObjectTypeEnum,
    Padding(1),
    "data" / Optional(PascalString(VarInt)),
    Terminated
)

# DELETE OBJECT
DeleteObjectCommandRequest = Struct(
    "opcode" / Const(0x04, Byte),
    "id" / VariableLengthIDAdapter(),
)

DeleteObjectCommandResponse = Struct(
    "opcode" / Const(0x04, Byte),
    "id" / VariableLengthIDAdapter(),
    "status" / Int8sb,
    Terminated
)


# RESET
ResetCommandRequest = Struct(
    "opcode" / Const(0x0B, Byte),
    "flags" / FlagsEnum(Byte,
                        erase_eeprom=1,
                        hard_reset=2,
                        default=0)
)



import unittest
from construct import *
from construct.lib import *

# 0301060F0C09776655443322110010F601000000

import logging

LOGGER = logging.getLogger(__name__)

import codecs
temp_sensor = OneWireTempSensor()
temp_sensor.settings.offset = 123
temp_sensor.settings.address = bytes([0x08, 0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01])
# temp_sensor.settings.address = bytes([0x28, 0x9E, 0x6C, 0xFF, 0x08, 0x00, 0x00, 0x42])

# print(codecs.encode(temp_sensor.SerializeToString(), 'hex'))

reset_and_erase_cmd = ResetCommandRequest.build(dict(flags=dict(erase_eeprom=True, hard_reset=True)))
create_temp_sensor = CreateObjectCommandRequest.build(dict(id=[0], type="TEMPERATURE_SENSOR", data=temp_sensor.SerializeToString()))
create_profile_cmd = CreateProfileCommandRequest.build(dict())
list_objects = ListObjectsCommandRequest.build({"profile_id": 0})
read_sensor_value = ReadValueCommandRequest.build({"id": [0], 'type':"TEMPERATURE_SENSOR"})
delete_temp_sensor = DeleteObjectCommandRequest.build({"id": [0]})
activate_profile = ActivateProfileCommandRequest.build({"profile_id": 0})

print(create_temp_sensor)
print(codecs.encode(create_temp_sensor, 'hex'))
exit(0)

cmds = [create_profile_cmd, activate_profile, list_objects, create_temp_sensor, list_objects]
# cmds = [reset_and_erase_cmd]
# cmds = [create_profile_cmd]

# cmds = [list_objects]
# cmds = [create_temp_sensor, list_objects]
# cmds = [delete_temp_sensor, create_temp_sensor, list_objects]

import serial

from construct.lib import hexlify

import coloredlogs
coloredlogs.install(level="DEBUG")

class ResponseDecoder:
    def accept(self, msg):
        LOGGER.debug("<-- {0} / {1}".format(msg, hexlify(msg)))

        res = CBoxCommand.parse(msg)
        if res.opcode == "READ_VALUE":
            print("<-- READ VALUE")
            decoded = ReadValueCommandResponse.parse(msg)
            print(decoded)
            sens = OneWireTempSensor()
            sens.ParseFromString(decoded.data)
            print("Is Connected? {0}".format(sens.state.connected))
            print("Temperature: {0}".format(sens.state.value/256.0))

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


decoder = ResponseDecoder()

if __name__ == "__main__":
    import io
    import binascii

    with serial.Serial("/dev/ttyACM0", timeout=2) as ser:
        sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser), newline="\r\n")

        for cmd in cmds:
            print("--> {0}".format(cmd))
            ser.write(codecs.encode(cmd, "hex"))
            ser.write(b"\n")

        for line in sio.readlines():
            line = line.replace(' ', '')
            line = line.strip("\n")
            line = line.strip("\r")
            LOGGER.info(decoder.accept(binascii.unhexlify(line)))

        ser.close()
