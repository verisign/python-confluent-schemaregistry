import unittest2 as unittest
import data_gen
import setup_test_path

import struct

from avro import schema
from confluent.schemaregistry.serializers import MessageSerializer, Util
from confluent.schemaregistry.client import MockSchemaRegistryClient

class TestMessageSerializer(unittest.TestCase):

    def setUp(self):
        # need to set up the serializer
        self.client = MockSchemaRegistryClient()
        self.ms = MessageSerializer(self.client)

    def assertMessageIsSame(self, message, expected, schema_id):
        self.assertTrue(message)
        self.assertTrue(len(message) > 5)
        magic,sid = struct.unpack('>bI',message[0:5])
        self.assertEqual(magic, 0)
        self.assertEqual(sid, schema_id)
        decoded = self.ms.decode_message(message)
        self.assertTrue(decoded)
        self.assertEqual(decoded, expected)

    def test_encode_with_schema_id(self):
        adv = Util.parse_schema_from_string(data_gen.ADVANCED_SCHEMA)
        basic = Util.parse_schema_from_string(data_gen.BASIC_SCHEMA)
        subject = 'test'
        schema_id = self.client.register(subject, basic)

        records = data_gen.BASIC_ITEMS
        for record in records:
            message = self.ms.encode_record_with_schema_id(schema_id, record)
            self.assertMessageIsSame(message, record, schema_id)

        subject = 'test_adv'
        adv_schema_id = self.client.register(subject, adv)
        self.assertNotEqual(adv_schema_id, schema_id)
        records = data_gen.ADVANCED_ITEMS
        for record in records:
            message = self.ms.encode_record_with_schema_id(adv_schema_id, record)
            self.assertMessageIsSame(message, record, adv_schema_id)


    def test_encode_record_for_topic(self):
        topic = 'test'
        basic = Util.parse_schema_from_string(data_gen.BASIC_SCHEMA)
        subject = 'test-value'
        schema_id = self.client.register(subject, basic)

        records = data_gen.BASIC_ITEMS
        for record in records:
            message = self.ms.encode_record_for_topic(topic, record)
            self.assertMessageIsSame(message, record ,schema_id)

    def test_encode_record_with_schema(self):
        topic = 'test'
        basic = Util.parse_schema_from_string(data_gen.BASIC_SCHEMA)
        subject = 'test-value'
        schema_id = self.client.register(subject, basic)
        records = data_gen.BASIC_ITEMS
        for record in records:
            message = self.ms.encode_record_with_schema(topic, basic, record)
            self.assertMessageIsSame(message, record ,schema_id)

def suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestMessageSerializer)
