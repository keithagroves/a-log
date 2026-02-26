# Copyright © 2012-2023 alog contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

Feature: Using the installed keyring

    Scenario: Storing a password in keyring
        Given we use the config "multiple.yaml"
        And we have a keyring
        When we run "alog simple --encrypt" and enter
            """
            sabertooth
            sabertooth
            Y
            """
        Then the config for journal "simple" should contain "encrypt: true"
        When we run "alog simple -n 1"
        Then the output should contain "2013-06-10 15:40 Life is good"


    Scenario: Encrypt journal with no keyring backend and do not store in keyring
        Given we use the config "simple.yaml"
        When we run "alog test entry"
        And we run "alog --encrypt" and enter
            """
            password
            password
            n
            """
        Then we should get no error
        And the output should not contain "Failed to retrieve keyring"


    Scenario: Encrypt journal with no keyring backend and do store in keyring
        Given we use the config "simple.yaml"
        When we run "alog test entry"
        And we run "alog --encrypt" and enter
            """
            password
            password
            y
            """
        Then we should get no error
        And the output should not contain "Failed to retrieve keyring"
        # @todo add step to check contents of keyring


    @todo
    Scenario: Open an encrypted journal with wrong password in keyring
    # This should ask the user for the password after the keyring fails


    @todo
    Scenario: Decrypt journal with password in keyring


    @todo
    Scenario: Decrypt journal without a keyring


    Scenario: Encrypt journal when keyring exists but fails
        Given we use the config "simple.yaml"
        And we have a failed keyring
        When we run "alog --encrypt" and enter
            """
            this password will not be saved in keyring
            this password will not be saved in keyring
            y
            """
        Then the output should contain "Failed to retrieve keyring"
        And we should get no error
        And we should be prompted for a password
        And the config for journal "default" should contain "encrypt: true"


    Scenario: Decrypt journal when keyring exists but fails
        Given we use the config "encrypted.yaml"
        And we have a failed keyring
        And we use the password "bad doggie no biscuit" if prompted
        When we run "alog --decrypt"
        Then the error output should contain "Failed to retrieve keyring"
        And we should get no error
        And we should be prompted for a password
        And the output should contain "Journal decrypted"
        And the config for journal "default" should contain "encrypt: false"
        When we run "alog --short"
        Then we should not be prompted for a password
        And the output should be
            """
            2013-06-09 15:39 My first entry.
            2013-06-10 15:40 Life is good.
            """


    Scenario: Open encrypted journal when keyring exists but fails
    # This should ask the user for the password after the keyring fails
        Given we use the config "encrypted.yaml"
        And we have a failed keyring
        And we use the password "bad doggie no biscuit" if prompted
        When we run "alog -n 1"
        Then we should get no error
        And we should be prompted for a password
        And the output should contain "Failed to retrieve keyring"
        And the output should contain "2013-06-10 15:40 Life is good"


    Scenario: Mistyping your password
        Given we use the config "simple.yaml"
        When we run "alog --encrypt" and enter
            """
            swordfish
            sordfish
            """
        Then we should be prompted for a password
        And the output should contain "Passwords did not match"
        And the config for journal "default" should not contain "encrypt: true"
        When we run "alog --short"
        Then the output should be
            """
            2013-06-09 15:39 My first entry.
            2013-06-10 15:40 Life is good.
            """


    Scenario: Mistyping your password, then getting it right
        Given we use the config "simple.yaml"
        When we run "alog --encrypt" and enter
            """
            swordfish
            sordfish
            swordfish
            swordfish
            n
            """
        Then we should be prompted for a password
        And the output should contain "Passwords did not match"
        And the output should contain "Journal encrypted"
        And the config for journal "default" should contain "encrypt: true"
        When we run "alog -1" and enter "swordfish"
        Then we should be prompted for a password
        And the output should contain "2013-06-10 15:40 Life is good"

