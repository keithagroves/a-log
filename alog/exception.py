# Copyright © 2012-2023 alog contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

from typing import TYPE_CHECKING

from alog.output import print_msg

if TYPE_CHECKING:
    from alog.messages import Message
    from alog.messages import MsgText


class AlogException(Exception):
    """Common exceptions raised by alog."""

    def __init__(self, *messages: "Message"):
        self.messages = messages

    def print(self) -> None:
        for msg in self.messages:
            print_msg(msg)

    def has_message_text(self, message_text: "MsgText"):
        return any([m.text == message_text for m in self.messages])
