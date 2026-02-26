# Copyright © 2012-2023 alog contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

from typing import TYPE_CHECKING

from alog.plugins.text_exporter import TextExporter
from alog.plugins.util import get_journal_frequency_one_level

if TYPE_CHECKING:
    from alog.journals import Entry
    from alog.journals import Journal


class DatesExporter(TextExporter):
    """This Exporter lists dates and their respective counts, for heatingmapping etc."""

    names = ["dates"]
    extension = "dates"

    @classmethod
    def export_entry(cls, entry: "Entry"):
        raise NotImplementedError

    @classmethod
    def export_journal(cls, journal: "Journal") -> str:
        """Returns dates and their frequencies for an entire journal."""
        date_counts = get_journal_frequency_one_level(journal)
        result = "\n".join(f"{date}, {count}" for date, count in date_counts.items())
        return result
