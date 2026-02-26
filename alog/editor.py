# Copyright © 2012-2023 alog contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from alog.exception import AlogException
from alog.messages import Message
from alog.messages import MsgStyle
from alog.messages import MsgText
from alog.os_compat import on_windows
from alog.os_compat import split_args
from alog.output import print_msg
from alog.path import absolute_path
from alog.path import get_templates_path


def get_text_from_editor(config: dict, template: str = "") -> str:
    suffix = ".alog"
    if config["template"]:
        template_filename = Path(config["template"]).name
        suffix = "-" + template_filename
    filehandle, tmpfile = tempfile.mkstemp(prefix="alog", text=True, suffix=suffix)
    os.close(filehandle)

    with open(tmpfile, "w", encoding="utf-8") as f:
        if template:
            f.write(template)

    try:
        subprocess.call(split_args(config["editor"]) + [tmpfile])
    except FileNotFoundError:
        raise AlogException(
            Message(
                MsgText.EditorMisconfigured,
                MsgStyle.ERROR,
                {"editor_key": config["editor"]},
            )
        )

    with open(tmpfile, "r", encoding="utf-8") as f:
        raw = f.read()
    os.remove(tmpfile)

    if not raw:
        raise AlogException(Message(MsgText.NoTextReceived, MsgStyle.NORMAL))

    return raw


def get_text_from_stdin() -> str:
    print_msg(
        Message(
            MsgText.WritingEntryStart,
            MsgStyle.TITLE,
            {
                "how_to_quit": (
                    MsgText.HowToQuitWindows if on_windows() else MsgText.HowToQuitLinux
                )
            },
        )
    )

    try:
        raw = sys.stdin.read()
    except KeyboardInterrupt:
        logging.error("Append mode: keyboard interrupt")
        raise AlogException(
            Message(MsgText.KeyboardInterruptMsg, MsgStyle.ERROR_ON_NEW_LINE),
            Message(MsgText.JournalNotSaved, MsgStyle.WARNING),
        )

    return raw


def get_template_path(template_path: str, alog_template_dir: str) -> str:
    actual_template_path = os.path.join(alog_template_dir, template_path)
    if not os.path.exists(actual_template_path):
        logging.debug(
            f"Couldn't open {actual_template_path}. "
            "Treating template path like a local / abs path."
        )
        actual_template_path = absolute_path(template_path)

    return actual_template_path


def read_template_file(template_path: str) -> str:
    """
    Reads the template file given a template path in this order:

        * Check $XDG_DATA_HOME/alog/templates/template_path.
        * Check template_arg as an absolute / relative path.

    If a file is found, its contents are returned as a string.
    If not, a AlogException is raised.
    """

    alog_template_dir = get_templates_path()
    actual_template_path = get_template_path(template_path, alog_template_dir)

    try:
        with open(actual_template_path, encoding="utf-8") as f:
            template_data = f.read()
            return template_data
    except FileNotFoundError:
        raise AlogException(
            Message(
                MsgText.CantReadTemplate,
                MsgStyle.ERROR,
                {
                    "template_path": template_path,
                    "actual_template_path": actual_template_path,
                    "alog_template_dir": str(alog_template_dir) + os.sep,
                },
            )
        )
