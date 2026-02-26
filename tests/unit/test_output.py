# Copyright © 2012-2023 alog contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

from unittest.mock import Mock
from unittest.mock import patch

from alog.messages import Message
from alog.output import print_msg


@patch("alog.output.print_msgs")
def test_print_msg_calls_print_msgs_as_list_with_style(print_msgs):
    test_msg = Mock(Message)
    print_msg(test_msg)
    print_msgs.assert_called_once_with([test_msg], style=test_msg.style)


@patch("alog.output.print_msgs")
def test_print_msg_calls_print_msgs_with_kwargs(print_msgs):
    test_msg = Mock(Message)
    kwargs = {
        "delimter": "test delimiter 🤡",
        "get_input": True,
        "hide_input": True,
        "some_rando_arg": "💩",
    }
    print_msg(test_msg, **kwargs)
    print_msgs.assert_called_once_with([test_msg], style=test_msg.style, **kwargs)
