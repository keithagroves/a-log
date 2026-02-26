# Copyright © 2012-2023 alog contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

Feature: Build process

    Scenario: Version numbers should stay in sync
        Given we use the config "simple.yaml"
        When we run "alog --version"
        Then we should get no error
        And the output should contain pyproject.toml version
