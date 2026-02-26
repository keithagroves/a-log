# Copyright © 2012-2023 alog contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

import sys
from typing import TYPE_CHECKING

from alog.exception import AlogException
from alog.messages import Message
from alog.messages import MsgStyle
from alog.messages import MsgText
from alog.output import print_msg

if TYPE_CHECKING:
    from alog.journals import Journal


class ALOGImporter:
    """This plugin imports entries from other alog files."""

    names = ["alog"]

    @staticmethod
    def import_(journal: "Journal", input: str | None = None) -> None:
        """Imports from an existing file if input is specified, and
        standard input otherwise."""
        old_cnt = len(journal.entries)
        if input:
            with open(input, "r", encoding="utf-8") as f:
                other_journal_txt = f.read()
        else:
            try:
                other_journal_txt = sys.stdin.read()
            except KeyboardInterrupt:
                raise AlogException(
                    Message(MsgText.KeyboardInterruptMsg, MsgStyle.ERROR_ON_NEW_LINE),
                    Message(MsgText.ImportAborted, MsgStyle.WARNING),
                )

        journal.import_(other_journal_txt)
        new_cnt = len(journal.entries)
        journal.write()
        print_msg(
            Message(
                MsgText.ImportSummary,
                MsgStyle.NORMAL,
                {
                    "count": new_cnt - old_cnt,
                    "journal_name": journal.name,
                },
            )
        )
