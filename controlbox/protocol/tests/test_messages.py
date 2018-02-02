from unittest import TestCase

from construct import Container

from controlbox.protocol.commands import (
    VariableLengthIDAdapter,
    CreateObjectCommandRequest
)


class TestReadValue(TestCase):
    def test_variable_length_id_one_byte(self):
        adapter = VariableLengthIDAdapter()
        assert adapter.parse(b"\x01") == [1]

        assert adapter.build([1]) == b"\x01"

    def test_variable_length_id_multiple_bytes(self):
        adapter = VariableLengthIDAdapter()
        assert adapter.parse(b"\x81\x02") == [1, 2]

        assert adapter.build([1, 2]) == b"\x81\x02"
        assert adapter.parse(b"\x01\x02") == [1]


class TestCreateObject(TestCase):
    def test_create_object(self):
        obj_data = b"\x01\x03"
        assert CreateObjectCommandRequest.build(dict(id=[1], type="TEMPERATURE_SENSOR", data=obj_data)) == b"\x03\x01\x06\x02\x01\x03"

        assert CreateObjectCommandRequest.parse(b"\x03\x01\x06\x02\x01\x02") == Container(opcode=3)(id=[1])(type='TEMPERATURE_SENSOR')(data=[1, 2])
