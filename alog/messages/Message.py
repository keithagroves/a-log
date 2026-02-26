# Copyright © 2012-2023 alog contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

from typing import TYPE_CHECKING
from typing import Mapping
from typing import NamedTuple

from alog.messages.MsgStyle import MsgStyle

if TYPE_CHECKING:
    from alog.messages.MsgText import MsgText


class Message(NamedTuple):
    text: "MsgText"
    style: MsgStyle = MsgStyle.NORMAL
    params: Mapping = {}
