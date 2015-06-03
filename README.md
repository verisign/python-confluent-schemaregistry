# Python Schema Registry Client

A Python client used to interact with the confluent schema registry.  Support for 2.6 and 2.7.  This also works within a virtual env.

The API is heavily based off of the existing Java API found [here](https://github.com/confluentinc/schema-registry).

# Example Usage


```python
from confluent.schemaregistry.client import CachedSchemaRegistryClient
from confluent.schemaregistry.serializers import MessageSerializer, Util

# Note that some methods may throw exceptions if
# the registry cannot be reached, decoding/encoding fails,
# or IO fails

# some helper methods in util to get a schema
avro_schema = Util.parse_schema_from_file('/path/to/schema.avsc')
avro_schema = Util.parse_schema_from_string(open('/path/to/schema.avsc').read())

# Initialize the client
client = CachedSchemaRegistryClient(url='http://registry.host')

# Schema operations

# register a schema for a subject
schema_id = client.register('my_subject', avro_schema)

# fetch a schema by ID
avro_schema = client.get_by_id(schema_id)

# get the latest schema info for a subject
schema_id,avro_schema,schema_version = client.get_latest_schema('my_subject')

# get the version of a schema
schema_version = client.get_version('my_subject', avro_schema)

# Compatibility tests
is_compatible = client.test_compatibility('my_subject', another_schema)

# One of NONE, FULL, FORWARD, BACKWARD
new_level = client.update_compatibility('my_subject','NONE')
current_level = client.get_compatibility('my_subject')

# Message operations

# encode a record to put onto kafka
serializer = MessageSerializer(client)
record = get_obj_to_put_into_kafka()

# use the schema id directly
encoded = serializer.encode_record_with_schema_id(schema_id, record)
# use an existing schema and topic
# this will register the schema to the right subject based
# on the topic name and then serialize
encoded = serializer.encode_record_with_schema('my_topic', avro_schema, record)

# encode a record with the latest schema for the topic
# this is not efficient as it queries for the latest
# schema each time
encoded = serializer.encode_record_for_topic('my_kafka_topic', record)


# decode a message from kafka
message = get_message_from_kafka()
decoded_object = serializer.decode_message(message)


```

# Running Tests

```
pip install unittest2
unit2 discover -s test
```

Tests use unittest2 due to unittest being different between 2.6 and 2.7.

# License

The project is licensed under the Apache 2 license.
