"""
Tests for metadata module.
"""

from dataclasses import dataclass, field

from varlord.metadata import (
    get_all_field_keys,
    get_all_fields_info,
    get_field_info,
)


def test_get_all_fields_info_basic():
    """Test basic field info extraction."""

    @dataclass
    class Config:
        api_key: str = field(metadata={"description": "API key"})
        host: str = field(default="localhost", metadata={"optional": True, "description": "Host"})
        port: int = field(
            default=8000,
        )

    fields = get_all_fields_info(Config)

    assert len(fields) == 3

    # Check host field
    host_field = next(f for f in fields if f.name == "host")
    assert host_field.normalized_key == "host"
    assert host_field.default == "localhost"
    assert host_field.optional is True
    assert host_field.required is False
    assert host_field.description == "Host"

    # Check api_key field
    api_key_field = next(f for f in fields if f.name == "api_key")
    assert api_key_field.normalized_key == "api_key"
    assert api_key_field.required is True
    assert api_key_field.optional is False


def test_get_all_fields_info_nested():
    """Test nested field info extraction."""

    @dataclass
    class DBConfig:
        host: str = field()
        port: int = field(
            default=5432,
        )

    @dataclass
    class AppConfig:
        api_key: str = field()
        db: DBConfig = field()

    fields = get_all_fields_info(AppConfig)

    # Should have 4 fields: api_key, db (parent), db.host, db.port
    # Note: parent field 'db' is also included
    assert len(fields) == 4

    field_keys = {f.normalized_key for f in fields}
    # Note: parent field 'db' is also included
    assert field_keys == {"api_key", "db", "db.host", "db.port"}

    # Check nested field
    db_host = next(f for f in fields if f.normalized_key == "db.host")
    assert db_host.name == "host"
    assert db_host.required is True


def test_get_all_field_keys():
    """Test field key extraction."""

    @dataclass
    class DBConfig:
        host: str = field()
        port: int = field()

    @dataclass
    class AppConfig:
        api_key: str = field()
        db: DBConfig = field()

    keys = get_all_field_keys(AppConfig)
    # Note: parent field 'db' is also included
    assert keys == {"api_key", "db", "db.host", "db.port"}


def test_get_field_info():
    """Test getting specific field info."""

    @dataclass
    class Config:
        host: str = field(
            default="localhost",
        )
        port: int = field(
            default=8000,
        )

    field_info = get_field_info(Config, "host")
    assert field_info is not None
    assert field_info.name == "host"
    assert field_info.default == "localhost"

    # Test nested field
    @dataclass
    class DBConfig:
        host: str = field()

    @dataclass
    class AppConfig:
        db: DBConfig = field()

    field_info = get_field_info(AppConfig, "db.host")
    assert field_info is not None
    assert field_info.normalized_key == "db.host"
    assert field_info.required is True
