# Copyright © 2012-2023 alog contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

"""
Functions in this file are standalone commands. All standalone commands are split into
two categories depending on whether they require the config to be loaded to be able to
run.

1. "preconfig" commands don't require the config at all, and can be run before the
   config has been loaded.
2. "postconfig" commands require to config to have already been loaded, parsed, and
   scoped before they can be run.

Also, please note that all (non-builtin) imports should be scoped to each function to
avoid any possible overhead for these standalone commands.
"""

import argparse
import logging
import platform
import sys

from alog.config import cmd_requires_valid_journal_name
from alog.exception import AlogException
from alog.messages import Message
from alog.messages import MsgStyle
from alog.messages import MsgText
from alog.output import print_msg


def preconfig_diagnostic(_) -> None:
    from alog import __title__
    from alog import __version__

    print(
        f"{__title__}: {__version__}\n"
        f"Python: {sys.version}\n"
        f"OS: {platform.system()} {platform.release()}"
    )


def preconfig_version(_) -> None:
    import textwrap

    from alog import __title__
    from alog import __version__

    output = f"""
    {__title__} {__version__}

    Copyright © 2012-2023 alog contributors

    This is free software, and you are welcome to redistribute it under certain
    conditions; for details, see: https://www.gnu.org/licenses/gpl-3.0.html
    """

    output = textwrap.dedent(output).strip()

    print(output)


def postconfig_list(args: argparse.Namespace, config: dict, **_) -> int:
    from alog.output import list_journals

    print(list_journals(config, args.export))

    return 0


@cmd_requires_valid_journal_name
def postconfig_import(args: argparse.Namespace, config: dict, **_) -> int:
    from alog.journals import open_journal
    from alog.plugins import get_importer

    # Requires opening the journal
    journal = open_journal(args.journal_name, config)

    format = args.export if args.export else "alog"

    if (importer := get_importer(format)) is None:
        raise AlogException(
            Message(
                MsgText.ImporterNotFound,
                MsgStyle.ERROR,
                {"format": format},
            )
        )

    importer.import_(journal, args.filename)

    return 0


@cmd_requires_valid_journal_name
def postconfig_encrypt(
    args: argparse.Namespace, config: dict, original_config: dict
) -> int:
    """
    Encrypt a journal in place, or optionally to a new file
    """
    from alog.config import update_config
    from alog.install import save_config
    from alog.journals import open_journal

    # Open the journal
    journal = open_journal(args.journal_name, config)

    if hasattr(journal, "can_be_encrypted") and not journal.can_be_encrypted:
        raise AlogException(
            Message(
                MsgText.CannotEncryptJournalType,
                MsgStyle.ERROR,
                {
                    "journal_name": args.journal_name,
                    "journal_type": journal.__class__.__name__,
                },
            )
        )

    # If journal is encrypted, create new password
    logging.debug("Clearing encryption method...")

    if journal.config["encrypt"] is True:
        logging.debug("Journal already encrypted. Re-encrypting...")
        print(f"Journal {journal.name} is already encrypted. Create a new password.")
        journal.encryption_method.clear()
    else:
        journal.config["encrypt"] = True
        journal.encryption_method = None

    journal.write(args.filename)

    print_msg(
        Message(
            MsgText.JournalEncryptedTo,
            MsgStyle.NORMAL,
            {"path": args.filename or journal.config["journal"]},
        )
    )

    # Update the config, if we encrypted in place
    if not args.filename:
        update_config(
            original_config, {"encrypt": True}, args.journal_name, force_local=True
        )
        save_config(original_config)

    return 0


@cmd_requires_valid_journal_name
def postconfig_decrypt(
    args: argparse.Namespace, config: dict, original_config: dict
) -> int:
    """Decrypts to file. If filename is not set, we encrypt the journal file itself."""
    from alog.config import update_config
    from alog.install import save_config
    from alog.journals import open_journal

    journal = open_journal(args.journal_name, config)

    logging.debug("Clearing encryption method...")
    journal.config["encrypt"] = False
    journal.encryption_method = None

    journal.write(args.filename)
    print_msg(
        Message(
            MsgText.JournalDecryptedTo,
            MsgStyle.NORMAL,
            {"path": args.filename or journal.config["journal"]},
        )
    )

    # Update the config, if we decrypted in place
    if not args.filename:
        update_config(
            original_config, {"encrypt": False}, args.journal_name, force_local=True
        )
        save_config(original_config)

    return 0


@cmd_requires_valid_journal_name
def postconfig_index_search(
    args: argparse.Namespace, config: dict, **_
) -> int:
    """Build or rebuild semantic search index for the selected journal."""
    from alog.journals import open_journal
    from alog.search import build_index

    journal = open_journal(args.journal_name, config)
    build_index(journal, config)
    print_msg(Message(MsgText.SemanticIndexBuilt, MsgStyle.NORMAL))

    return 0
