"""
Basic utilities for handling avro schemas
"""
from avro import schema

def parse_schema_from_string(schema_str):
    """Parse a schema given a schema string"""
    return schema.parse(schema_str)

def parse_schema_from_file(schema_path):
    """Parse a schema from a file path"""
    with open(schema_path) as f:
        return parse_schema_from_string(f.read())
