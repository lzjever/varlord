"""
Tests for key normalization and field name validation.
"""

import pytest
from dataclasses import dataclass
from varlord.sources.base import normalize_key
from varlord.sources.defaults import Defaults


class TestNormalizeKey:
    """Test normalize_key function with various edge cases."""

    def test_basic_cases(self):
        """Test basic normalization cases."""
        assert normalize_key("APP_HOST") == "app_host"
        assert normalize_key("APP_DB__HOST") == "app_db.host"  # Single _ before __ is preserved
        assert normalize_key("APP__DB__HOST") == "app.db.host"  # Double __ becomes .
        assert normalize_key("K8S_POD_NAME") == "k8s_pod_name"
        assert normalize_key("db__host") == "db.host"

    def test_empty_string(self):
        """Test empty string."""
        assert normalize_key("") == ""

    def test_single_underscore(self):
        """Test single underscore."""
        assert normalize_key("_") == "_"
        assert normalize_key("a_b") == "a_b"
        assert normalize_key("_a") == "_a"
        assert normalize_key("a_") == "a_"

    def test_double_underscore(self):
        """Test double underscore conversion."""
        assert normalize_key("__") == "."
        assert normalize_key("a__b") == "a.b"
        assert normalize_key("__a") == ".a"
        assert normalize_key("a__") == "a."

    def test_triple_underscore(self):
        """Test triple underscore (edge case).

        Note: ___ is processed as __ + _, so the first __ becomes ., leaving _.
        """
        assert normalize_key("___") == "._"  # __ becomes ., _ remains
        assert normalize_key("a___b") == "a._b"  # a + __ + _ + b
        assert normalize_key("___a") == "._a"  # __ + _ + a
        assert normalize_key("a___") == "a._"  # a + __ + _

    def test_quadruple_underscore(self):
        """Test quadruple underscore."""
        assert normalize_key("____") == ".."
        assert normalize_key("a____b") == "a..b"

    def test_multiple_double_underscores(self):
        """Test multiple double underscores."""
        assert normalize_key("a__b__c") == "a.b.c"
        assert normalize_key("a__b__c__d") == "a.b.c.d"
        assert normalize_key("__a__b__") == ".a.b."

    def test_mixed_underscores(self):
        """Test mixed single and double underscores."""
        assert normalize_key("a_b__c") == "a_b.c"
        assert normalize_key("a__b_c") == "a.b_c"
        assert normalize_key("a_b__c_d") == "a_b.c_d"

    def test_case_conversion(self):
        """Test case conversion."""
        assert normalize_key("APP_HOST") == "app_host"
        assert normalize_key("app_HOST") == "app_host"
        assert normalize_key("App_Host") == "app_host"
        assert normalize_key("APP_DB__HOST") == "app_db.host"  # Single _ preserved
        assert normalize_key("APP__DB__HOST") == "app.db.host"  # Double __ becomes .

    def test_only_underscores(self):
        """Test strings with only underscores."""
        assert normalize_key("_") == "_"
        assert normalize_key("__") == "."
        assert normalize_key("___") == "._"  # __ becomes ., _ remains
        assert normalize_key("____") == ".."  # Two __ become two .
        assert normalize_key("_____") == ".._"  # __ + __ + _ becomes . + . + _

    def test_leading_trailing_underscores(self):
        """Test leading and trailing underscores."""
        assert normalize_key("_a") == "_a"
        assert normalize_key("a_") == "a_"
        assert normalize_key("__a") == ".a"
        assert normalize_key("a__") == "a."
        assert normalize_key("_a_") == "_a_"
        assert normalize_key("__a__") == ".a."

    def test_real_world_examples(self):
        """Test real-world configuration examples."""
        assert normalize_key("APP_DB__HOST") == "app_db.host"  # Single _ before __ preserved
        assert normalize_key("APP__DB__HOST") == "app.db.host"  # Double __ becomes .
        assert normalize_key("APP_DB__PORT") == "app_db.port"
        assert normalize_key("K8S_POD_NAME") == "k8s_pod_name"
        assert normalize_key("API_TIMEOUT_SECONDS") == "api_timeout_seconds"
        assert normalize_key("REDIS__CACHE__TTL") == "redis.cache.ttl"


class TestDefaultsFieldValidation:
    """Test field name validation in Defaults source."""

    def test_valid_field_names(self):
        """Test that valid field names are accepted."""

        @dataclass
        class Config:
            host: str = "localhost"
            port: int = 8000
            k8s_pod_name: str = "pod"
            api_timeout: int = 30

        source = Defaults(model=Config)
        config = source.load()
        assert "host" in config
        assert "k8s_pod_name" in config

    def test_double_underscore_in_field_name_raises_error(self):
        """Test that double underscore in field name raises ValueError."""

        @dataclass
        class Config:
            db__host: str = "localhost"

        with pytest.raises(ValueError, match="contains double underscores"):
            Defaults(model=Config)

    def test_multiple_double_underscores_raises_error(self):
        """Test that multiple double underscores raise error."""

        @dataclass
        class Config:
            a__b__c: str = "value"

        with pytest.raises(ValueError, match="contains double underscores"):
            Defaults(model=Config)

    def test_triple_underscore_in_field_name_raises_error(self):
        """Test that triple underscore (which contains __) raises error."""

        @dataclass
        class Config:
            a___b: str = "value"

        with pytest.raises(ValueError, match="contains double underscores"):
            Defaults(model=Config)

    def test_single_underscore_allowed(self):
        """Test that single underscores are allowed."""

        @dataclass
        class Config:
            k8s_pod_name: str = "pod"
            api_timeout: int = 30
            _private: str = "private"

        source = Defaults(model=Config)
        config = source.load()
        assert "k8s_pod_name" in config
        assert "api_timeout" in config

    def test_error_message_includes_field_name(self):
        """Test that error message includes the problematic field name."""

        @dataclass
        class Config:
            db__host: str = "localhost"

        with pytest.raises(ValueError) as exc_info:
            Defaults(model=Config)

        error_msg = str(exc_info.value)
        assert "db__host" in error_msg
        assert "Config" in error_msg

    def test_nested_dataclass_allowed(self):
        """Test that nested dataclasses are allowed (they use dot notation, not __)."""
        from dataclasses import field

        @dataclass
        class DBConfig:
            host: str = "localhost"
            port: int = 5432

        @dataclass
        class Config:
            db: DBConfig = field(default_factory=DBConfig)
            api_timeout: int = 30

        source = Defaults(model=Config)
        config = source.load()
        # Nested dataclasses are handled separately, not through field name normalization
        assert "api_timeout" in config

    def test_multiple_fields_with_double_underscore(self):
        """Test that error is raised even if only one field has double underscore."""

        @dataclass
        class Config:
            host: str = "localhost"
            db__host: str = "localhost"  # This should trigger error
            port: int = 8000

        with pytest.raises(ValueError, match="contains double underscores"):
            Defaults(model=Config)
