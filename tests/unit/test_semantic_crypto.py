# Copyright © 2012-2023 jrnl contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

import numpy as np

from jrnl.search.crypto import IndexKeyCrypto
from jrnl.search.crypto import pack_payload
from jrnl.search.crypto import unpack_payload


def test_index_crypto_roundtrip():
    crypto = IndexKeyCrypto("secret-password")
    data = b"hello semantic index"

    encrypted = crypto.encrypt_payload(data)
    decrypted = crypto.decrypt_payload(encrypted)

    assert decrypted == data


def test_pack_unpack_payload_roundtrip():
    embedding = np.array([0.1, -0.2, 0.3, 0.4], dtype=np.float32)
    payload = pack_payload(
        embedding=embedding,
        entry_date="2026-02-14T12:00:00",
        bhash="deadbeef",
        indexed_at="2026-02-14T12:01:00",
    )

    unpacked = unpack_payload(payload, dimensions=4)

    np.testing.assert_allclose(unpacked["embedding"], embedding)
    assert unpacked["entry_date"] == "2026-02-14T12:00:00"
    assert unpacked["body_hash"] == "deadbeef"
    assert unpacked["indexed_at"] == "2026-02-14T12:01:00"
