"""
pytest 配置和 fixtures
"""

import os
import sys
from pathlib import Path

# Add project root to Python path so tests can import varlord
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest  # noqa: E402


# Dependency availability checks
def has_etcd():
    """Check if etcd3 is available."""
    try:
        import etcd3  # noqa: F401

        return True
    except (ImportError, TypeError):
        # TypeError can occur with protobuf version incompatibility
        return False


def pytest_configure(config):
    """Register custom markers for optional dependencies."""
    config.addinivalue_line("markers", "requires_etcd: mark test as requiring etcd3 package")


def pytest_collection_modifyitems(config, items):
    """Automatically deselect tests that require unavailable dependencies.

    Note: dotenv, yaml, and toml are core dependencies and should not be checked here.
    Only etcd is an optional dependency.
    """
    # Lazy dependency availability - only check when needed
    etcd_available = None  # Cache for etcd availability

    deselected = []
    selected = []

    for item in items:
        # Check if test requires etcd
        requires_etcd = any(
            marker.name == "requires_etcd" or marker.name == "etcd"
            for marker in item.iter_markers()
        )

        # Check if test file name suggests it needs etcd
        if not requires_etcd:
            test_file = str(item.fspath)
            if "etcd" in test_file.lower() and (
                "test_etcd" in test_file or "etcd_integration" in test_file
            ):
                requires_etcd = True

        # Only check dependency availability if the test actually requires it
        should_deselect = False
        reason = None

        if requires_etcd:
            # Lazy check: only check etcd availability when needed
            if etcd_available is None:
                etcd_available = has_etcd()
            if not etcd_available:
                should_deselect = True
                reason = "etcd3 not installed or incompatible"

        if should_deselect:
            deselected.append(item)
            item.add_marker(pytest.mark.skip(reason=reason))
        else:
            selected.append(item)

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        # Print summary
        print(f"\n⚠️  Deselected {len(deselected)} test(s) due to missing dependencies:")
        for item in deselected[:10]:  # Show first 10
            print(f"   - {item.nodeid}")
        if len(deselected) > 10:
            print(f"   ... and {len(deselected) - 10} more")
        print()


@pytest.fixture
def temp_file(tmp_path):
    """提供临时文件路径"""
    return str(tmp_path / "test_file.env")


@pytest.fixture
def temp_dir(tmp_path):
    """提供临时目录路径"""
    return str(tmp_path)


@pytest.fixture
def cleanup_files():
    """清理函数，用于删除测试文件"""
    files_to_cleanup = []

    def _add_file(filepath):
        files_to_cleanup.append(filepath)

    yield _add_file

    # 清理
    for filepath in files_to_cleanup:
        if os.path.exists(filepath):
            os.remove(filepath)


@pytest.fixture
def sample_config_model():
    """提供示例配置模型（所有字段都是 optional，有默认值）"""
    from dataclasses import dataclass, field

    @dataclass(frozen=True)
    class SampleConfig:
        host: str = field(
            default="127.0.0.1",
        )
        port: int = field(
            default=8000,
        )
        debug: bool = field(
            default=False,
        )
        timeout: float = field(
            default=30.0,
        )

    return SampleConfig


@pytest.fixture
def datadir():
    """提供测试 fixtures 目录路径。

    Usage:
        def test_yaml_load(datadir):
            yaml_path = datadir / "yaml" / "config_valid.yaml"
            ...
    """
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def yaml_datadir(datadir):
    """提供 YAML fixtures 目录路径"""
    return datadir / "yaml"


@pytest.fixture
def json_datadir(datadir):
    """提供 JSON fixtures 目录路径"""
    return datadir / "json"


@pytest.fixture
def toml_datadir(datadir):
    """提供 TOML fixtures 目录路径"""
    return datadir / "toml"


@pytest.fixture
def env_datadir(datadir):
    """提供 ENV fixtures 目录路径"""
    return datadir / "env"
