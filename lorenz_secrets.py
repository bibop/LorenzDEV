#!/usr/bin/env python3
"""
🔐 LORENZ Secrets Manager
===========================================================

Gestione sicura delle credenziali e API keys.

Backends supportati:
1. macOS Keychain (preferito su Mac)
2. File criptato con Fernet (fallback cross-platform)
3. Environment variables (legacy)

Utilizzo:
    from lorenz_secrets import SecretsManager

    secrets = SecretsManager()
    secrets.set("OPENAI_API_KEY", "sk-...")
    api_key = secrets.get("OPENAI_API_KEY")

Autore: Claude Code
Data: 2026-01-14
"""

import os
import sys
import json
import base64
import hashlib
import getpass
import logging
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

# Cryptography imports
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("⚠️ cryptography not installed. Run: pip install cryptography")

# macOS Keychain imports
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    logger.warning("⚠️ keyring not installed. Run: pip install keyring")


# ============================================================================
# CONSTANTS
# ============================================================================

SERVICE_NAME = "LORENZ"
SECRETS_DIR = Path.home() / ".lorenz" / "secrets"
ENCRYPTED_FILE = SECRETS_DIR / "credentials.enc"
SALT_FILE = SECRETS_DIR / ".salt"

# Known API keys for LORENZ
KNOWN_SECRETS = [
    "OPENAI_API_KEY",
    "CLAUDE_API_KEY",
    "PERPLEXITY_API_KEY",
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "TAVILY_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "NAS_PASSWORD",
    "SSH_KEY_PASSPHRASE",
]


# ============================================================================
# KEYCHAIN BACKEND (macOS/Linux/Windows native)
# ============================================================================

class KeychainBackend:
    """
    Backend che usa il keychain nativo del sistema operativo.
    - macOS: Keychain
    - Linux: Secret Service (GNOME Keyring, KWallet)
    - Windows: Credential Manager
    """

    def __init__(self, service_name: str = SERVICE_NAME):
        self.service_name = service_name
        self.available = KEYRING_AVAILABLE

        if self.available:
            logger.info(f"🔐 Keychain backend initialized (service: {service_name})")

    def set(self, key: str, value: str) -> bool:
        """Store a secret in keychain"""
        if not self.available:
            return False
        try:
            keyring.set_password(self.service_name, key, value)
            logger.info(f"✅ Stored '{key}' in system keychain")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to store in keychain: {e}")
            return False

    def get(self, key: str) -> Optional[str]:
        """Retrieve a secret from keychain"""
        if not self.available:
            return None
        try:
            value = keyring.get_password(self.service_name, key)
            if value:
                logger.debug(f"🔑 Retrieved '{key}' from keychain")
            return value
        except Exception as e:
            logger.error(f"❌ Failed to retrieve from keychain: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete a secret from keychain"""
        if not self.available:
            return False
        try:
            keyring.delete_password(self.service_name, key)
            logger.info(f"🗑️ Deleted '{key}' from keychain")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete from keychain: {e}")
            return False

    def list_keys(self) -> List[str]:
        """List all stored keys (checks known secrets)"""
        if not self.available:
            return []

        stored = []
        for key in KNOWN_SECRETS:
            if self.get(key):
                stored.append(key)
        return stored


# ============================================================================
# ENCRYPTED FILE BACKEND
# ============================================================================

class EncryptedFileBackend:
    """
    Backend che usa un file criptato con Fernet (AES-128-CBC).
    La master password viene usata per derivare la chiave di cifratura.
    """

    def __init__(self, file_path: Path = ENCRYPTED_FILE):
        self.file_path = file_path
        self.salt_path = SALT_FILE
        self.available = CRYPTO_AVAILABLE
        self._fernet: Optional[Fernet] = None
        self._data: Dict[str, str] = {}
        self._unlocked = False

        # Ensure directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if self.available:
            logger.info(f"🔐 Encrypted file backend initialized")

    def _get_or_create_salt(self) -> bytes:
        """Get or create encryption salt"""
        if self.salt_path.exists():
            return self.salt_path.read_bytes()
        else:
            salt = os.urandom(16)
            self.salt_path.write_bytes(salt)
            # Protect salt file
            os.chmod(self.salt_path, 0o600)
            return salt

    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        salt = self._get_or_create_salt()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,  # OWASP recommended
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def unlock(self, password: str) -> bool:
        """Unlock the encrypted storage with master password"""
        if not self.available:
            logger.error("❌ Cryptography not available")
            return False

        try:
            key = self._derive_key(password)
            self._fernet = Fernet(key)

            # Try to load existing data
            if self.file_path.exists():
                encrypted_data = self.file_path.read_bytes()
                decrypted = self._fernet.decrypt(encrypted_data)
                self._data = json.loads(decrypted.decode())
                logger.info(f"✅ Unlocked encrypted storage ({len(self._data)} secrets)")
            else:
                self._data = {}
                logger.info("✅ Created new encrypted storage")

            self._unlocked = True
            return True

        except Exception as e:
            logger.error(f"❌ Failed to unlock: {e}")
            self._fernet = None
            self._unlocked = False
            return False

    def _save(self):
        """Save encrypted data to file"""
        if not self._fernet or not self._unlocked:
            return False

        try:
            json_data = json.dumps(self._data, indent=2)
            encrypted = self._fernet.encrypt(json_data.encode())
            self.file_path.write_bytes(encrypted)
            # Protect file
            os.chmod(self.file_path, 0o600)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save: {e}")
            return False

    def set(self, key: str, value: str) -> bool:
        """Store a secret"""
        if not self._unlocked:
            logger.error("❌ Storage not unlocked")
            return False

        self._data[key] = value
        if self._save():
            logger.info(f"✅ Stored '{key}' in encrypted file")
            return True
        return False

    def get(self, key: str) -> Optional[str]:
        """Retrieve a secret"""
        if not self._unlocked:
            return None
        return self._data.get(key)

    def delete(self, key: str) -> bool:
        """Delete a secret"""
        if not self._unlocked:
            return False

        if key in self._data:
            del self._data[key]
            if self._save():
                logger.info(f"🗑️ Deleted '{key}' from encrypted file")
                return True
        return False

    def list_keys(self) -> List[str]:
        """List all stored keys"""
        if not self._unlocked:
            return []
        return list(self._data.keys())

    @property
    def is_unlocked(self) -> bool:
        return self._unlocked


# ============================================================================
# SECRETS MANAGER (Main Interface)
# ============================================================================

class SecretsManager:
    """
    🔐 Main secrets manager for LORENZ.

    Priorità di lettura:
    1. Environment variables (override everything)
    2. macOS Keychain / System keyring
    3. Encrypted file (requires unlock)

    Priorità di scrittura:
    1. macOS Keychain (if available)
    2. Encrypted file (fallback)
    """

    def __init__(self, use_keychain: bool = True, use_encrypted: bool = True):
        self.keychain = KeychainBackend() if use_keychain else None
        self.encrypted = EncryptedFileBackend() if use_encrypted else None
        self._master_password: Optional[str] = None

        logger.info("🔐 SecretsManager initialized")
        logger.info(f"   Keychain: {'✅' if self.keychain and self.keychain.available else '❌'}")
        logger.info(f"   Encrypted: {'✅' if self.encrypted and self.encrypted.available else '❌'}")

    def unlock(self, password: str = None) -> bool:
        """
        Unlock encrypted storage.
        If password is None, prompts interactively.
        """
        if not self.encrypted:
            return True  # Nothing to unlock

        if password is None:
            password = getpass.getpass("🔐 Enter LORENZ master password: ")

        self._master_password = password
        return self.encrypted.unlock(password)

    def set(self, key: str, value: str, prefer_keychain: bool = True) -> bool:
        """
        Store a secret.

        Args:
            key: Secret name (e.g., "OPENAI_API_KEY")
            value: Secret value
            prefer_keychain: If True, store in keychain first
        """
        success = False

        # Try keychain first
        if prefer_keychain and self.keychain and self.keychain.available:
            success = self.keychain.set(key, value)
            if success:
                return True

        # Fallback to encrypted file
        if self.encrypted and self.encrypted.is_unlocked:
            success = self.encrypted.set(key, value)

        return success

    def get(self, key: str, default: str = None) -> Optional[str]:
        """
        Retrieve a secret.

        Priority:
        1. Environment variable
        2. Keychain
        3. Encrypted file
        4. Default value
        """
        # 1. Check environment first (allows override)
        env_value = os.environ.get(key)
        if env_value:
            logger.debug(f"🔑 '{key}' from environment")
            return env_value

        # 2. Check keychain
        if self.keychain and self.keychain.available:
            value = self.keychain.get(key)
            if value:
                return value

        # 3. Check encrypted file
        if self.encrypted and self.encrypted.is_unlocked:
            value = self.encrypted.get(key)
            if value:
                return value

        # 4. Return default
        return default

    def delete(self, key: str) -> bool:
        """Delete a secret from all backends"""
        success = False

        if self.keychain and self.keychain.available:
            if self.keychain.delete(key):
                success = True

        if self.encrypted and self.encrypted.is_unlocked:
            if self.encrypted.delete(key):
                success = True

        return success

    def list_secrets(self) -> Dict[str, str]:
        """
        List all secrets with their storage location.
        Returns dict of {key: location}
        """
        secrets = {}

        # Check environment
        for key in KNOWN_SECRETS:
            if os.environ.get(key):
                secrets[key] = "environment"

        # Check keychain
        if self.keychain and self.keychain.available:
            for key in self.keychain.list_keys():
                if key not in secrets:
                    secrets[key] = "keychain"

        # Check encrypted file
        if self.encrypted and self.encrypted.is_unlocked:
            for key in self.encrypted.list_keys():
                if key not in secrets:
                    secrets[key] = "encrypted_file"

        return secrets

    def get_status(self) -> Dict:
        """Get secrets manager status for diagnostics"""
        secrets = self.list_secrets()

        return {
            "keychain_available": self.keychain.available if self.keychain else False,
            "encrypted_available": self.encrypted.available if self.encrypted else False,
            "encrypted_unlocked": self.encrypted.is_unlocked if self.encrypted else False,
            "total_secrets": len(secrets),
            "secrets_by_location": {
                "environment": len([k for k, v in secrets.items() if v == "environment"]),
                "keychain": len([k for k, v in secrets.items() if v == "keychain"]),
                "encrypted_file": len([k for k, v in secrets.items() if v == "encrypted_file"]),
            },
            "configured_keys": list(secrets.keys()),
            "missing_keys": [k for k in KNOWN_SECRETS if k not in secrets],
        }

    def export_to_env(self) -> str:
        """
        Export all secrets as environment variable format.
        NEVER logs the actual values!
        """
        lines = ["# LORENZ Secrets Export", f"# Generated: {datetime.now().isoformat()}", ""]

        for key in KNOWN_SECRETS:
            value = self.get(key)
            if value:
                # Mask value for security
                masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "****"
                lines.append(f"# {key}={masked}")
                lines.append(f'export {key}="{value}"')
                lines.append("")

        return "\n".join(lines)

    def import_from_env_file(self, file_path: str, store_in: str = "keychain") -> int:
        """
        Import secrets from a .env file.

        Args:
            file_path: Path to .env file
            store_in: "keychain" or "encrypted"

        Returns:
            Number of secrets imported
        """
        count = 0
        prefer_keychain = store_in == "keychain"

        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    # Parse key=value or export key="value"
                    if line.startswith('export '):
                        line = line[7:]

                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")

                    if key in KNOWN_SECRETS and value:
                        if self.set(key, value, prefer_keychain=prefer_keychain):
                            count += 1
                            logger.info(f"✅ Imported: {key}")

        return count


# ============================================================================
# CLI INTERFACE
# ============================================================================

def cli_main():
    """Interactive CLI for managing secrets"""
    import argparse

    parser = argparse.ArgumentParser(description="🔐 LORENZ Secrets Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command
    subparsers.add_parser("list", help="List all stored secrets")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get a secret")
    get_parser.add_argument("key", help="Secret key name")

    # Set command
    set_parser = subparsers.add_parser("set", help="Set a secret")
    set_parser.add_argument("key", help="Secret key name")
    set_parser.add_argument("--value", help="Secret value (prompts if not provided)")
    set_parser.add_argument("--keychain", action="store_true", help="Store in keychain")

    # Delete command
    del_parser = subparsers.add_parser("delete", help="Delete a secret")
    del_parser.add_argument("key", help="Secret key name")

    # Import command
    import_parser = subparsers.add_parser("import", help="Import from .env file")
    import_parser.add_argument("file", help="Path to .env file")
    import_parser.add_argument("--to", choices=["keychain", "encrypted"], default="keychain")

    # Export command
    subparsers.add_parser("export", help="Export secrets as env format")

    # Status command
    subparsers.add_parser("status", help="Show secrets manager status")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    # Initialize manager
    secrets = SecretsManager()

    # Unlock encrypted storage if needed
    if secrets.encrypted and secrets.encrypted.available:
        # Check for password in environment first
        master_password = os.environ.get("LORENZ_MASTER_PASSWORD")

        if not ENCRYPTED_FILE.exists():
            print("🔐 Creating new encrypted storage...")
            if master_password:
                print("   (Using LORENZ_MASTER_PASSWORD from environment)")
                secrets.unlock(master_password)
            else:
                try:
                    password = getpass.getpass("Enter new master password: ")
                    confirm = getpass.getpass("Confirm master password: ")
                    if password != confirm:
                        print("❌ Passwords don't match!")
                        return 1
                    secrets.unlock(password)
                except EOFError:
                    print("ℹ️ No TTY available. Set LORENZ_MASTER_PASSWORD env var or use --password")
                    print("   Continuing with keychain-only mode...")
        else:
            if master_password:
                secrets.unlock(master_password)
            else:
                try:
                    secrets.unlock()
                except EOFError:
                    print("ℹ️ No TTY available. Continuing with keychain-only mode...")

    if args.command == "list":
        print("\n🔐 LORENZ Secrets")
        print("=" * 50)
        secrets_map = secrets.list_secrets()

        if not secrets_map:
            print("(No secrets stored)")
        else:
            for key, location in sorted(secrets_map.items()):
                icon = {"environment": "🌍", "keychain": "🔑", "encrypted_file": "📁"}
                print(f"  {icon.get(location, '❓')} {key} [{location}]")

        print("\n📋 Missing secrets:")
        status = secrets.get_status()
        for key in status["missing_keys"]:
            print(f"  ❌ {key}")

    elif args.command == "get":
        value = secrets.get(args.key)
        if value:
            # Mask middle of value
            if len(value) > 10:
                masked = value[:5] + "..." + value[-5:]
            else:
                masked = "****"
            print(f"🔑 {args.key} = {masked}")
            print(f"   (Full value copied to clipboard)" if sys.platform == "darwin" else "")
            # Copy to clipboard on macOS
            if sys.platform == "darwin":
                import subprocess
                subprocess.run(["pbcopy"], input=value.encode(), check=True)
        else:
            print(f"❌ Secret '{args.key}' not found")

    elif args.command == "set":
        value = args.value
        if not value:
            value = getpass.getpass(f"Enter value for {args.key}: ")

        if secrets.set(args.key, value, prefer_keychain=args.keychain):
            print(f"✅ Stored: {args.key}")
        else:
            print(f"❌ Failed to store: {args.key}")

    elif args.command == "delete":
        if secrets.delete(args.key):
            print(f"🗑️ Deleted: {args.key}")
        else:
            print(f"❌ Failed to delete: {args.key}")

    elif args.command == "import":
        count = secrets.import_from_env_file(args.file, store_in=args.to)
        print(f"✅ Imported {count} secrets to {args.to}")

    elif args.command == "export":
        print(secrets.export_to_env())

    elif args.command == "status":
        status = secrets.get_status()
        print("\n🔐 Secrets Manager Status")
        print("=" * 50)
        print(f"  Keychain available: {'✅' if status['keychain_available'] else '❌'}")
        print(f"  Encrypted available: {'✅' if status['encrypted_available'] else '❌'}")
        print(f"  Encrypted unlocked: {'✅' if status['encrypted_unlocked'] else '❌'}")
        print(f"\n  Total secrets: {status['total_secrets']}")
        print(f"    - Environment: {status['secrets_by_location']['environment']}")
        print(f"    - Keychain: {status['secrets_by_location']['keychain']}")
        print(f"    - Encrypted: {status['secrets_by_location']['encrypted_file']}")

    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(cli_main())
