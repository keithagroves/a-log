# Copyright © 2012-2023 alog contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

import logging

from alog.encryption.BaseEncryption import BaseEncryption
from alog.exception import AlogException
from alog.keyring import get_keyring_password
from alog.messages import Message
from alog.messages import MsgStyle
from alog.messages import MsgText
from alog.prompt import create_password
from alog.prompt import prompt_password


class BasePasswordEncryption(BaseEncryption):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        logging.debug("start")
        self._attempts: int = 0
        self._max_attempts: int = 3
        self._password: str = ""
        self._check_keyring: bool = True

    @property
    def check_keyring(self) -> bool:
        return self._check_keyring

    @check_keyring.setter
    def check_keyring(self, value: bool) -> None:
        self._check_keyring = value

    @property
    def password(self) -> str | None:
        return self._password

    @password.setter
    def password(self, value: str) -> None:
        self._password = value

    def clear(self):
        self.password = None
        self.check_keyring = False

    def encrypt(self, text: str) -> bytes:
        logging.debug("encrypting")
        if not self.password:
            if self.check_keyring and (
                keyring_pw := get_keyring_password(self._journal_name)
            ):
                self.password = keyring_pw

            if not self.password:
                self.password = create_password(self._journal_name)

        return self._encrypt(text)

    def decrypt(self, text: bytes) -> str:
        logging.debug("decrypting")
        if not self.password:
            if self.check_keyring and (
                keyring_pw := get_keyring_password(self._journal_name)
            ):
                self.password = keyring_pw

            if not self.password:
                self._prompt_password()

        while (result := self._decrypt(text)) is None:
            self._prompt_password()

        return result

    def _prompt_password(self) -> None:
        if self._attempts >= self._max_attempts:
            raise AlogException(
                Message(MsgText.PasswordMaxTriesExceeded, MsgStyle.ERROR)
            )

        first_try = self._attempts == 0
        self.password = prompt_password(first_try=first_try)
        self._attempts += 1
