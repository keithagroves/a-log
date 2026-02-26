# Copyright © 2012-2023 alog contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

Feature: Journals iteracting with the file system in a way that users can see

    Scenario: Adding entries to a Folder journal should generate date files
        Given we use the config "empty_folder.yaml"
        When we run "alog 23 July 2013: Testing folder journal."
        Then we should get no error
        And the journal directory should contain
            """
            2013/07/23.txt
            """

    Scenario: Adding multiple entries to a Folder journal should generate multiple date files
        Given we use the config "empty_folder.yaml"
        When we run "alog 23 July 2013: Testing folder journal."
        And we run "alog 3/7/2014: Second entry of journal."
        Then we should get no error
        And the journal directory should contain
            """
            2013/07/23.txt
            """

    Scenario: If the journal and its parent directory don't exist, they should be created
        Given we use the config "missing_directory.yaml"
        Then the journal should not exist
        When we run "alog This is a new entry in my journal"
        Then the journal should exist
        When we run "alog -99 --short"
        Then the output should contain "This is a new entry in my journal"

    Scenario: If the journal file doesn't exist, then it should be created
        Given we use the config "missing_journal.yaml"
        Then the journal should not exist
        When we run "alog This is a new entry in my journal"
        Then the journal should exist
        When we run "alog -99 --short"
        Then the output should contain "This is a new entry in my journal"

    @on_posix
    Scenario: If the directory for a Folder journal ending in a slash ('/') doesn't exist, then it should be created
        Given we use the config "missing_directory.yaml"
        Then the journal "endslash" directory should not exist
        When we run "alog endslash This is a new entry in my journal"
        Then the journal "endslash" directory should exist
        When we run "alog endslash -1"
        Then the output should contain "This is a new entry in my journal"

    @on_win
    Scenario: If the directory for a Folder journal ending in a backslash ('\') doesn't exist, then it should be created
        Given we use the config "missing_directory.yaml"
        Then the journal "endbackslash" directory should not exist
        When we run "alog endbackslash This is a new entry in my journal"
        Then the journal "endbackslash" directory should exist
        When we run "alog endbackslash -1"
        Then the output should contain "This is a new entry in my journal"

    Scenario: Creating journal with relative path should update to absolute path
        Given we use no config
        When we run "alog hello world" and enter
            """
            test.txt
            n
            \n
            """
        Then the output should contain "Journal 'default' created"
        When we change directory to "subfolder"
        And we run "alog -n 1"
        Then the output should contain "hello world"

    Scenario: the temporary filename suffix should default to ".alog"
        Given we use the config "editor.yaml"
        When we run "alog --edit"
        Then the editor should have been called
        Then the editor filename should end with ".alog"

    Scenario: the temporary filename suffix should be "-{template_filename}"
        Given we use the config "editor_markdown_extension.yaml"
        When we run "alog --edit"
        Then the editor filename should end with "-extension.md"
