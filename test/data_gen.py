import random
import os
import os.path

NAMES = ['stefan','melanie','nick','darrel','kent','simon']
AGES = list(range(1,10)) + [None]

def get_schema_path(fname):
    dname = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(dname, fname)

def load_schema_file(fname):
    fname = get_schema_path(fname)
    with open(fname) as f:
        return f.read()

BASIC_SCHEMA = load_schema_file('basic_schema.avsc')

def create_basic_item(i):
    return {
        'name' : random.choice(NAMES) + '-' + str(i),
        'number' : random.choice(AGES)
    }

BASIC_ITEMS = map(create_basic_item, range(1,20))

ADVANCED_SCHEMA = load_schema_file('adv_schema.avsc')

def create_adv_item(i):
    friends = map(create_basic_item, range(1,3))
    family = map(create_basic_item, range(1,3))
    basic = create_basic_item(i)
    basic['family'] = dict(map(lambda bi: (bi['name'],bi), family))
    basic['friends'] = dict(map(lambda bi: (bi['name'],bi), friends))
    return basic

ADVANCED_ITEMS = map(create_adv_item, range(1, 20))

from avro import schema
from avro.datafile import DataFileReader, DataFileWriter
from avro.io import DatumReader, DatumWriter
import json

def _write_items(base_name, schema_str, items):
    avro_schema = schema.parse(schema_str)
    avro_file = base_name + '.avro'
    with DataFileWriter(open(avro_file, "w"), DatumWriter(), avro_schema) as writer:
        for i in items:
            writer.append(i)
    writer.close
    return (avro_file)

def write_basic_items(base_name):
    return _write_items(base_name, BASIC_SCHEMA, BASIC_ITEMS)

def write_advanced_items(base_name):
    return _write_items(base_name, ADVANCED_SCHEMA, ADVANCED_ITEMS)

def cleanup(files):
    for f in files:
        try:
            os.remove(f)
        except OSError:
            pass

if __name__ == "__main__":
    write_advanced_items("advanced")
