# Copyright © 2012-2023 alog contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

Feature: Tagging
# See search.feature for tag-related searches
# And format.feature for tag-related output

    Scenario Outline: Tags should allow certain special characters such as /, +, #
        Given we use the config "<config_file>"
        When we run "alog 2020-09-26: This is an entry about @os/2 and @c++ and @c#"
        When we run "alog --tags -on 2020-09-26"
        Then we should get no error
        And the output should be
            """
            @os/2                : 1
            @c++                 : 1
            @c#                  : 1
            """

        Examples: configs
        | config_file        |
        | basic_onefile.yaml |
        | basic_folder.yaml  |
        | basic_dayone.yaml  |

    Scenario Outline: Emails addresses should not be parsed as tags
        Given we use the config "<config_file>"
        When we run "alog 2020-09-26: The email address test@example.com does not seem to work for me"
        When we run "alog 2020-09-26: The email address test@example.org also does not work for me"
        When we run "alog 2020-09-26: I tried test@example.org and test@example.edu too"
        When we run "alog --tags -on 2020-09-26"
        Then we should get no error
        And the output should be "[No tags found in journal.]"

        Examples: configs
        | config_file        |
        | basic_onefile.yaml |
        | basic_folder.yaml  |
        | basic_dayone.yaml  |

    Scenario Outline:  Entry can start and end with tags
        Given we use the config "<config_file>"
        When we run "alog 2020-09-26: @foo came over, we went to a @bar"
        When we run "alog --tags -on 2020-09-26"
        Then the output should be
            """
            @foo                 : 1
            @bar                 : 1
            """

        Examples: configs
        | config_file        |
        | basic_onefile.yaml |
        | basic_folder.yaml  |
        | basic_dayone.yaml  |
