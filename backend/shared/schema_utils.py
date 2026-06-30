import io
import json
import struct

import fastavro
import requests

MAGIC_BYTE = 0x00  # Confluent wire format identifier


def register_schema(schema_registry_url: str, subject: str, schema: dict) -> int:
    """Register an Avro schema under a subject. Returns the schema ID."""
    resp = requests.post(
        f"{schema_registry_url}/subjects/{subject}/versions",
        headers={"Content-Type": "application/vnd.schemaregistry.v1+json"},
        json={"schema": json.dumps(schema)},
    )
    resp.raise_for_status()
    return resp.json()["id"]


def get_schema_by_id(schema_registry_url: str, schema_id: int) -> dict:
    """Fetch an Avro schema from the registry by its ID."""
    resp = requests.get(f"{schema_registry_url}/schemas/ids/{schema_id}")
    resp.raise_for_status()
    return json.loads(resp.json()["schema"])


def serialize(data: dict, schema: dict, schema_id: int) -> bytes:
    """
    Serialize a dict to Confluent wire format:
      [magic byte (1)] + [schema_id (4)] + [avro bytes]
    """
    parsed = fastavro.parse_schema(schema)
    buf = io.BytesIO()
    buf.write(struct.pack(">bI", MAGIC_BYTE, schema_id))
    fastavro.schemaless_writer(buf, parsed, data)
    return buf.getvalue()


def deserialize(data: bytes, schema_registry_url: str) -> dict:
    """
    Deserialize Confluent wire format bytes back to a dict.
    Reads schema ID from the header, fetches schema, decodes Avro payload.
    """
    magic, schema_id = struct.unpack(">bI", data[:5])
    assert magic == MAGIC_BYTE, f"Unexpected magic byte: {magic}"
    schema = get_schema_by_id(schema_registry_url, schema_id)
    parsed = fastavro.parse_schema(schema)
    return fastavro.schemaless_reader(io.BytesIO(data[5:]), parsed)
