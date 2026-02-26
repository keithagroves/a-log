# Copyright © 2012-2023 alog contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

import datetime

import numpy as np

from alog.search.entry_id import body_hash
from alog.search.entry_id import entry_id
from alog.search.index import SemanticIndex


class DummyEntry:
    def __init__(self, date: datetime.datetime, title: str, body: str):
        self.date = date
        self.title = title
        self.body = body


class DummyJournal:
    def __init__(self, entries):
        self.entries = entries


def _make_entry(day: int, title: str, body: str):
    return DummyEntry(datetime.datetime(2026, 2, day, 9, 0, 0), title, body)


def test_semantic_index_search_returns_ranked_matches():
    index = SemanticIndex(":memory:", "test-model", 4)

    index.store(
        "a",
        np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32),
        "2026-02-01T09:00:00",
        "h1",
    )
    index.store(
        "b",
        np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32),
        "2026-02-02T09:00:00",
        "h2",
    )
    index.store(
        "c",
        np.array([0.9, 0.1, 0.0, 0.0], dtype=np.float32),
        "2026-02-03T09:00:00",
        "h3",
    )

    query = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    results = index.search(query, top_k=2)

    assert results[0][0] == "a"
    assert results[1][0] == "c"

    index.close()


def test_semantic_index_sync_add_update_delete():
    one = _make_entry(1, "One", "Body one")
    two = _make_entry(2, "Two", "Body two")

    index = SemanticIndex(":memory:", "test-model", 4)

    # Initial sync: both add
    diff = index.sync(DummyJournal([one, two]))
    assert len(diff["add"]) == 2
    assert len(diff["update"]) == 0
    assert len(diff["delete"]) == 0

    # Store both in index
    batch = []
    for entry in [one, two]:
        batch.append(
            (
                entry_id(entry),
                np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32),
                entry.date.isoformat(),
                body_hash(entry),
            )
        )
    index.store_batch(batch)

    # Change body of second, remove first, add third
    two.body = "Body two updated"
    three = _make_entry(3, "Three", "Body three")
    diff = index.sync(DummyJournal([two, three]))

    assert len(diff["add"]) == 1
    assert diff["add"][0].title == "Three"
    assert len(diff["update"]) == 1
    assert diff["update"][0].title == "Two"
    assert len(diff["delete"]) == 1

    index.close()
