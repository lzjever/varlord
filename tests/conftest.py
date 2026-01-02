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
    except ImportError:
        return False


def has_dotenv():
    """Check if python-dotenv is available."""
    try:
        from dotenv import dotenv_values  # noqa: F401

        return True
    except ImportError:
        return False


def pytest_configure(config):
    """Register custom markers for optional dependencies."""
    config.addinivalue_line("markers", "requires_etcd: mark test as requiring etcd3 package")
    config.addinivalue_line(
        "markers", "requires_dotenv: mark test as requiring python-dotenv package"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically deselect tests that require unavailable dependencies."""
    # Check which dependencies are available
    etcd_available = has_etcd()
    dotenv_available = has_dotenv()

    deselected = []
    selected = []

    for item in items:
        # Check if test requires etcd
        requires_etcd = any(
            marker.name == "requires_etcd" or marker.name == "etcd"
            for marker in item.iter_markers()
        )

        # Check if test requires dotenv
        requires_dotenv = any(
            marker.name == "requires_dotenv" or marker.name == "dotenv"
            for marker in item.iter_markers()
        )

        # Check if test file name suggests it needs etcd
        if not requires_etcd:
            test_file = str(item.fspath)
            if "etcd" in test_file.lower() and (
                "test_etcd" in test_file or "etcd_integration" in test_file
            ):
                requires_etcd = True

        # Check if test file name suggests it needs dotenv
        if not requires_dotenv:
            test_file = str(item.fspath)
            if "dotenv" in test_file.lower() and "test_sources_dotenv" in test_file:
                requires_dotenv = True

        # Deselect if dependencies are missing
        should_deselect = False
        reason = None

        if requires_etcd and not etcd_available:
            should_deselect = True
            reason = "etcd3 not installed"
        elif requires_dotenv and not dotenv_available:
            should_deselect = True
            reason = "python-dotenv not installed"

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
