<!--
Copyright © 2012-2023 alog contributors
License: https://www.gnu.org/licenses/gpl-3.0.html
-->

# Getting started

## Installation

The easiest way to install `alog` is using
[pipx](https://pipx.pypa.io/stable/installation/)
with [Python](https://www.python.org/) 3.10+:

``` sh
pipx install alog
```

!!! tip
     Do not use `sudo` while installing `alog`. This may lead to path issues.

The first time you run `alog` you will be asked where your journal file
should be created and whether you wish to encrypt it.

## Quickstart

To make a new entry, just type

``` text
alog yesterday: Called in sick. Used the time to clean, and spent 4h on writing my book.
```

and hit return. `yesterday:` will be interpreted as a time stamp.
Everything until the first sentence mark (`.?!:`) will be interpreted as
the title, the rest as the body. In your journal file, the result will
look like this:

``` output
2012-03-29 09:00 Called in sick.
Used the time to clean the house and spent 4h on writing my book.
```

If you just call `alog`, you will be prompted to compose your entry -
but you can also [configure](advanced.md) *alog* to use your external editor.
