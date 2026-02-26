# Copyright © 2012-2023 alog contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

import datetime

import numpy as np

from alog.search.crypto import IndexKeyCrypto
from alog.search.index import SemanticIndex


def test_encrypted_index_store_and_search_roundtrip():
    crypto = IndexKeyCrypto("password")
    index = SemanticIndex(":memory:", "test-model", 4, crypto=crypto)

    index.store(
        "a",
        np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32),
        "2026-02-01T09:00:00",
        "h1",
    )
    index.store(
        "b",
        np.array([0.9, 0.1, 0.0, 0.0], dtype=np.float32),
        "2026-02-02T09:00:00",
        "h2",
    )

    query = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    results = index.search(query, top_k=2)

    assert results[0][0] == "a"
    assert results[1][0] == "b"

    index.close()
