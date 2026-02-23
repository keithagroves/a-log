# Copyright © 2012-2023 jrnl contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

"""Per-embedding encryption for encrypted journals.

When a journal is encrypted, the semantic index encrypts each embedding
individually using a separate key derived from the same password. This
prevents the index from leaking semantic information about entries.

Key design decisions:
- Uses a DIFFERENT PBKDF2 salt than Jrnlv2Encryption — compromising the
  index key does not yield the journal key
- Uses the SAME password — no additional password to remember
- Per-row encryption — each embedding is independently encrypted,
  preserving SQLite's incremental write capability
- Uses `cryptography` which is already a jrnl dependency
"""

import base64
import struct

import numpy as np
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# NOTE: Import order is intentionally grouped for readability; keep aligned with
# project isort settings in environments where ruff/isort is available.


# Different salt from the journal encryption (Jrnlv2Encryption uses its own)
_INDEX_SALT = b"\xa3\x91\xf7\x4b\xe2\x0c\x9d\x1a\xb8\x6e\x53\x72\xd4\x08\xaf\xc1"


class IndexKeyCrypto:
    """Derives a separate encryption key for the semantic index
    from the journal password."""

    def __init__(self, password: str):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=_INDEX_SALT,
            iterations=100_000,
            backend=default_backend(),
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
        self._fernet = Fernet(key)

    def encrypt_payload(self, data: bytes) -> bytes:
        """Encrypt a packed payload (embedding + metadata)."""
        return self._fernet.encrypt(data)

    def decrypt_payload(self, token: bytes) -> bytes:
        """Decrypt a packed payload.

        Raises:
            cryptography.fernet.InvalidToken: If the key is wrong or data is corrupt.
        """
        return self._fernet.decrypt(token)


def pack_payload(
    embedding: np.ndarray,
    entry_date: str,
    bhash: str,
    indexed_at: str,
) -> bytes:
    """Pack embedding + metadata into a single byte string.

    Format: [4 bytes meta length][meta bytes][embedding bytes]
    """
    emb_bytes = embedding.astype(np.float32).tobytes()
    meta = f"{entry_date}|{bhash}|{indexed_at}".encode("utf-8")
    return struct.pack("<I", len(meta)) + meta + emb_bytes


def unpack_payload(data: bytes, dimensions: int) -> dict:
    """Unpack a payload back into components.

    Returns:
        dict with keys: embedding (np.ndarray), entry_date, body_hash, indexed_at
    """
    meta_len = struct.unpack("<I", data[:4])[0]
    meta = data[4 : 4 + meta_len].decode("utf-8")
    entry_date, bhash, indexed_at = meta.split("|")
    emb = np.frombuffer(data[4 + meta_len :], dtype=np.float32).copy()
    return {
        "embedding": emb,
        "entry_date": entry_date,
        "body_hash": bhash,
        "indexed_at": indexed_at,
    }
