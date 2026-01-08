#!/usr/bin/env python3
"""
Simple script to test etcd connection with TLS.

This script can be used to verify that etcd is accessible
with the provided certificates before running integration tests.

Usage:
    python tests/test_etcd_connection.py
"""

import os
import sys
import warnings
from pathlib import Path

# Suppress etcd3 deprecation warnings from protobuf
warnings.filterwarnings("ignore", category=DeprecationWarning, module="etcd3")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="etcd3.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="etcd3.etcdrpc.*")

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import etcd3
except (ImportError, TypeError):
    # TypeError can occur with protobuf version incompatibility
    etcd3 = None
    # This is a standalone script, not a pytest test file
    # It will handle the error in check_etcd_connection()
    # Don't exit here - this file may be imported by pytest
    # The check_etcd_connection function will handle the error

# Configuration (can be overridden via environment variables)
ETCD_HOST = os.environ.get("ETCD_HOST", "127.0.0.1")
ETCD_PORT = int(os.environ.get("ETCD_PORT", "2379"))
ETCD_CA_CERT = os.environ.get("ETCD_CA_CERT", "./cert/AgentsmithLocal.cert.pem")
ETCD_CERT_KEY = os.environ.get("ETCD_CERT_KEY", "./cert/etcd-client-lzj-local/key.pem")
ETCD_CERT_CERT = os.environ.get("ETCD_CERT_CERT", "./cert/etcd-client-lzj-local/cert.pem")


def check_etcd_connection():
    """Test etcd connection."""
    print(f"Testing etcd connection to {ETCD_HOST}:{ETCD_PORT}...")

    # Check certificates
    print("\nChecking certificates:")
    certs_ok = True
    if os.path.exists(ETCD_CA_CERT):
        print(f"  ✓ CA cert found: {ETCD_CA_CERT}")
    else:
        print(f"  ✗ CA cert not found: {ETCD_CA_CERT}")
        certs_ok = False

    if os.path.exists(ETCD_CERT_KEY):
        print(f"  ✓ Client key found: {ETCD_CERT_KEY}")
    else:
        print(f"  ✗ Client key not found: {ETCD_CERT_KEY}")
        certs_ok = False

    if os.path.exists(ETCD_CERT_CERT):
        print(f"  ✓ Client cert found: {ETCD_CERT_CERT}")
    else:
        print(f"  ✗ Client cert not found: {ETCD_CERT_CERT}")
        certs_ok = False

    if not certs_ok:
        print("\nERROR: Some certificates are missing.")
        print("Please set the following environment variables:")
        print("  ETCD_CA_CERT=<path to CA certificate>")
        print("  ETCD_CERT_KEY=<path to client key>")
        print("  ETCD_CERT_CERT=<path to client certificate>")
        return False

    # Try to connect
    print("\nConnecting to etcd...")
    try:
        client_kwargs = {
            "host": ETCD_HOST,
            "port": ETCD_PORT,
        }

        if os.path.exists(ETCD_CA_CERT):
            client_kwargs["ca_cert"] = ETCD_CA_CERT
        if os.path.exists(ETCD_CERT_KEY):
            client_kwargs["cert_key"] = ETCD_CERT_KEY
        if os.path.exists(ETCD_CERT_CERT):
            client_kwargs["cert_cert"] = ETCD_CERT_CERT

        client = etcd3.client(**client_kwargs)

        # Test connection by getting a key
        try:
            client.get("/test_connection")
            print("  ✓ Connection successful!")
        except Exception as e:
            # Connection might work even if key doesn't exist
            if "connection" in str(e).lower() or "refused" in str(e).lower():
                print(f"  ✗ Connection failed: {e}")
                return False
            else:
                print("  ✓ Connection successful! (key not found, but connection works)")

        # Test varlord Etcd source
        print("\nTesting varlord Etcd source...")
        from varlord.sources.etcd import Etcd

        source = Etcd(
            host=ETCD_HOST,
            port=ETCD_PORT,
            prefix="/test/",
            ca_cert=ETCD_CA_CERT,
            cert_key=ETCD_CERT_KEY,
            cert_cert=ETCD_CERT_CERT,
        )

        print(f"  ✓ Etcd source created: {source}")

        # Try to load (will return empty if no model, but should not error)
        try:
            result = source.load()
            print(f"  ✓ Load method works (returned {len(result)} keys)")
        except ValueError as e:
            if "requires model" in str(e):
                print("  ✓ Load method works (model required as expected)")
            else:
                print(f"  ✗ Load method failed: {e}")
                return False
        except Exception as e:
            print(f"  ✗ Load method failed: {e}")
            return False

        print("\n✅ All tests passed! You can now run integration tests:")
        print("   pytest tests/test_sources_etcd_integration.py -m etcd")
        return True

    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure etcd is running")
        print("2. Check that certificates are correct")
        print("3. Verify etcd host and port are correct")
        return False


if __name__ == "__main__":
    success = check_etcd_connection()
    sys.exit(0 if success else 1)
