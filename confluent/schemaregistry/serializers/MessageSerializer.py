from avro import io
import StringIO
import json
import struct
import sys

from . import SerializerError

MAGIC_BYTE = 0

HAS_FAST = False
try:
    from fastavro.reader import read_data
    HAS_FAST = True
except:
    pass


class ContextStringIO(StringIO.StringIO):
    """
    Wrapper to allow use of StringIO via 'with' constructs.
    """
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()
        return False

class MessageSerializer(object):
    """
    A helper class that can serialize and deserialize messages
    that need to be encoded or decoded using the schema registry.

    All encode_* methods return a buffer that can be sent to kafka.
    All decode_* methods expect a buffer received from kafka.
    """
    def __init__(self, registry_client):
        self.registry_client = registry_client
        self.id_to_decoder_func = { }
        self.id_to_writers = { }

    def encode_record_with_schema(self, topic, schema, record, is_key=False):
        """
        Given a parsed avro schema, encode a record for the given topic.  The
        record is expected to be a dictionary.

        The schema is registered with the subject of 'topic-value'
        """
        if not isinstance(record, dict):
            raise SerializerError("record must be a dictionary")
        subject_suffix = ('-key' if is_key else '-value')
        # get the latest schema for the subject
        subject = topic + subject_suffix
        # register it
        try:
            schema_id = self.registry_client.register(subject, schema)
        except:
            schema_id = None

        if not schema_id:
            message = "Unable to retrieve schema id for subject %s" % (subject)
            raise SerializerError(message)

        # cache writer
        self.id_to_writers[schema_id] = io.DatumWriter(schema)
        return self.encode_record_with_schema_id(schema_id, record)

    # subject = topic + suffix
    def encode_record_for_topic(self, topic, record, is_key=False):
        """
        Encode a record for a given topic.

        This is expensive as it fetches the latest schema for a given topic.
        """
        if not isinstance(record, dict):
            raise SerializerError("record must be a dictionary")
        subject_suffix = ('-key' if is_key else '-value')
        # get the latest schema for the subject
        subject = topic + subject_suffix
        try:
            schema_id,schema,version = self.registry_client.get_latest_schema(subject)
        except ClientError as e:
            message = "Unable to retrieve schema id for subject %s" % (subject)
            raise SerializerError(message)
        else:
            # cache writer
            self.id_to_writers[schema_id] = io.DatumWriter(schema)
            return self.encode_record_with_schema_id(schema_id, record)

    def encode_record_with_schema_id(self, schema_id, record):
        """
        Encode a record with a given schema id.  The record must
        be a python dictionary.
        """
        if not isinstance(record, dict):
            raise SerializerError("record must be a dictionary")
        # use slow avro
        if schema_id not in self.id_to_writers:
            # get the writer + schema
            try:
                schema = self.registry_client.get_by_id(schema_id)
                if not schema:
                    raise SerializerError("Schema does not exist")
                self.id_to_writers[schema_id] = io.DatumWriter(schema)
            except ClientError as e:
                raise SerializerError("Error fetching schema from registry")

        # get the writer
        writer = self.id_to_writers[schema_id]
        with ContextStringIO() as outf:
            # write the header
            # magic byte
            outf.write(struct.pack('b',MAGIC_BYTE))
            # write the schema ID in network byte order (big end)
            outf.write(struct.pack('>I',schema_id))
            # write the record to the rest of it
            # Create an encoder that we'll write to
            encoder = io.BinaryEncoder(outf)
            # write the magic byte
            # write the object in 'obj' as Avro to the fake file...
            writer.write(record, encoder)

            return outf.getvalue()


    # Decoder support
    def _get_decoder_func(self, schema_id, payload):
        if schema_id in self.id_to_decoder_func:
            return self.id_to_decoder_func[schema_id]

        # fetch from schema reg
        try:
            schema = self.registry_client.get_by_id(schema_id)
        except:
            schema = None

        if not schema:
            err = "unable to fetch schema with id %d" % (schema_id)
            raise SerializerError(err)

        curr_pos = payload.tell()
        if HAS_FAST:
            # try to use fast avro
            try:
                schema_dict = schema.to_json()
                obj = read_data(payload, schema_dict)
                # here means we passed so this is something fastavro can do
                # seek back since it will be called again for the
                # same payload - one time hit

                payload.seek(curr_pos)
                decoder_func = lambda p: read_data(p, schema_dict)
                self.id_to_decoder_func[schema_id] = decoder_func
                return self.id_to_decoder_func[schema_id]
            except:
                pass

        # here means we should just delegate to slow avro
        # rewind
        payload.seek(curr_pos)
        avro_reader = io.DatumReader(schema)
        def decoder(p):
            bin_decoder = io.BinaryDecoder(p)
            return avro_reader.read(bin_decoder)

        self.id_to_decoder_func[schema_id] = decoder
        return self.id_to_decoder_func[schema_id]

    def decode_message(self, message):
        """
        Decode a message from kafka that has been encoded for use with
        the schema registry.
        """
        if len(message) <= 5:
            raise SerializerError("message is too small to decode")

        with ContextStringIO(message) as payload:
            magic,schema_id = struct.unpack('>bI',payload.read(5))
            if magic != MAGIC_BYTE:
                raise SerializerError("message does not start with magic byte")
            decoder_func = self._get_decoder_func(schema_id, payload)
            return decoder_func(payload)
