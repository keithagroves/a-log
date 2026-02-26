# Copyright © 2012-2023 alog contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

import datetime

from alog.search.entry_id import body_hash
from alog.search.entry_id import entry_id


class DummyEntry:
    def __init__(self, date: datetime.datetime, title: str, body: str):
        self.date = date
        self.title = title
        self.body = body


def test_entry_id_stable_for_same_date_title():
    date = datetime.datetime(2026, 2, 14, 12, 30, 0)
    a = DummyEntry(date, "Title", "Body one")
    b = DummyEntry(date, "Title", "Body two")

    assert entry_id(a) == entry_id(b)


def test_entry_id_changes_when_title_changes():
    date = datetime.datetime(2026, 2, 14, 12, 30, 0)
    a = DummyEntry(date, "Title A", "Body")
    b = DummyEntry(date, "Title B", "Body")

    assert entry_id(a) != entry_id(b)


def test_body_hash_changes_when_body_changes():
    date = datetime.datetime(2026, 2, 14, 12, 30, 0)
    a = DummyEntry(date, "Title", "Body one")
    b = DummyEntry(date, "Title", "Body two")

    assert body_hash(a) != body_hash(b)
