<!--
Copyright © 2012-2023 alog contributors
License: https://www.gnu.org/licenses/gpl-3.0.html
-->

# Basic Usage #

`alog` has two modes: **composing** and **viewing**. Whenever you don't enter
any arguments that start with a dash (`-`) or double-dash (`--`), you're in
composing mode, meaning that you can write your entry on the command line.

We intentionally break a convention on command line arguments: all arguments
starting with a _single dash_ (`-`) will _filter_ your journal before viewing
it. Filter arguments can be combined arbitrarily. Arguments with a _double dash_
(`--`) will _control_ how your journal is displayed or exported. Control
arguments are mutually exclusive (i.e., you can only specify one way to display
or export your journal at a time).

For a list of commands, enter `alog --help`.

## Composing Entries ##

Composing mode is entered by either starting `alog` without any arguments --
which will launch an external editor -- or by just writing an entry on the
command line:

```text
alog today at 3am: I just met Steve Buscemi in a bar! What a nice guy.
```

!!! note
    Most shells contain a certain number of reserved characters, such as `#` and
    `*`. These characters, as well as unbalanced single or double quotation
    marks, parentheses, and others, likely will cause problems. Although
    reserved characters can be escaped using `\`, this is not ideal for
    long-form writing. The solution: first enter `alog` and hit `return`. You
    can then enter the text of your journal entry. Alternatively, you can [use
    an external editor](./advanced.md).

You can also import an entry directly from a file:

```sh
alog < my_entry.txt
```

### Specifying Date and Time ###

If you don't specify a date and time (e.g., `alog finished writing letter to brother`), `alog` will create an entry using the current date and time. For retrospective entries, you can use a timestamp to tell `alog` where to put the entry. Timestamps can be entered using a variety of formats. Here are some that work:

- at 6am
- yesterday
- last monday
- sunday at noon
- 2 march 2012
- 7 apr
- 5/20/1998 at 23:42
- 2020-05-22T15:55-04:00

If you don't use a timestamp, `alog` will create an entry using the current
time. If you use a date only (no time), `alog` will use the default time
specified in your [configuration file](./reference-config-file.md#default_hour-and-default_minute).
Behind the scenes, `alog` reorganizes entries in chronological order.

### Using Tags ###

`alog` supports tags. The default tag symbol is `@` (largely because `#` is a
reserved character). You can specify your own tag symbol in the
[configuration file](./reference-config-file.md#tagsymbols). To use tags, preface the
desired tag with the symbol:

```sh
alog Had a wonderful day at the @beach with @Tom and @Anna.
```

Although you can use capitals while tagging an entry, searches by tag are
case-insensitive.

There is no limit to how many tags you can use in an entry.

### Starring Entries ###

To mark an entry as a favorite, simply "star" it using an asterisk (`*`):

```sh
alog last sunday *: Best day of my life.
```

If you don't want to add a date (i.e., you want the date to be entered as
_now_), the following options are equivalent:

- `alog *: Best day of my life.`
- `alog *Best day of my life.`
- `alog Best day of my life.*`

!!! note
    Make sure that the asterisk (`*`) is **not** surrounded by whitespaces.
    `alog Best day of my life! *` will not work because the `*` character has a
    special meaning in most shells.

## Viewing and Searching Entries ##

`alog` can display entries in a variety of ways.

To view all entries, enter:
```sh
alog -to today
```

`alog` provides several filtering commands, prefaced by a single dash (`-`), that
allow you to find a more specific range of entries. For example,

```sh
alog -n 10
```

lists the ten most recent entries. `alog -10` is even more concise and works the
same way. If you want to see all of the entries you wrote from the beginning of
last year until the end of this past March, you would enter

```sh
alog -from "last year" -to march
```

Filter criteria that use more than one word require surrounding quotes (`""`).

To see entries on a particular date, use `-on`:
```sh
alog -on yesterday
```

### Text Search ###

The `-contains` command displays all entries containing the text you enter after it.
This may be helpful when you're searching for entries and you can't remember if you
tagged any words when you wrote them.

You may realize that you use a word a lot and want to turn it into a tag in all
of your previous entries.

```sh
alog -contains "dogs" --edit
```

opens your external editor so that you can add a tag symbol (`@` by default) to
all instances of the word "dogs."

### Filtering by Tag ###

You can filter your journal entries by tag. For example,

```sh
alog @pinkie @WorldDomination
```

displays all entries in which either `@pinkie` or `@WorldDomination`
occurred. Tag filters can be combined with other filters:

```sh
alog -n 5 @pinkie -and @WorldDomination
```

displays the last five entries containing _both_ `@pinkie` _and_
`@worldDomination`. You can change which symbols you'd like to use for tagging
in the [configuration file](./reference-config-file.md#tagsymbols).

!!! note
    Entering `alog @pinkie @WorldDomination` will display entries in which both
    tags are present because, although no command line arguments are given, all
    of the input strings look like tags. `alog` will assume you want to filter
    by tag, rather than create a new entry that consists only of tags.

To view a list of all tags in the journal, enter:

```sh
alog --tags
```

### Viewing Starred Entries ###

To display only your favorite (starred) entries, enter

```sh
alog -starred
```

## Editing Entries ##

You can edit entries after writing them. This is particularly useful when your
journal file is encrypted. To use this feature, you need to have an external
editor configured in your [configuration file](./reference-config-file.md#editor). You
can also edit only the entries that match specific search criteria. For example,

```sh
alog -to 1950 @texas -and @history --edit
```

opens your external editor displaying all entries tagged with `@texas` and
`@history` that were written before 1950. After making changes, save and close
the file, and only those entries will be modified (and encrypted, if
applicable).

If you are using multiple journals, it's easy to edit specific entries from
specific journals. Simply prefix the filter string with the name of the journal.
For example,

```sh
alog work -n 1 --edit
```

opens the most recent entry in the 'work' journal in your external editor.

## Deleting Entries ##

The `--delete` command opens an interactive interface for deleting entries. The
date and title of each entry in the journal are presented one at a time, and you
can choose whether to keep or delete each entry.

If no filters are specified, `alog` will ask you to keep or delete each entry in
the entire journal, one by one. If there are a lot of entries in the journal, it
may be more efficient to filter entries before passing the `--delete` command.

Here's an example. Say you have a journal into which you've imported the last 12
years of blog posts. You use the `@book` tag a lot, and for some reason you want
to delete some, but not all, of the entries in which you used that tag, but only
the ones you wrote at some point in 2004 or earlier. You're not sure which
entries you want to keep, and you want to look through them before deciding.
This is what you might enter:

```sh
alog -to 2004 @book --delete
```

`alog` will show you only the relevant entries, and you can choose the ones you
want to delete.

You may want to delete _all_ of the entries containing `@book` that you wrote in
2004 or earlier. If there are dozens or hundreds, the easiest way would be to
use an external editor. Open an editor with the entries you want to delete...

```sh
alog -to 2004 @book --edit
```

...select everything, delete it, save and close, and all of those entries are
removed from the journal.

## Listing Journals ##

To list all of your journals:

```sh
alog --list
```

The journals displayed correspond to those specified in the `alog`
[configuration file](./reference-config-file.md#journals).

## Semantic Search ##

Semantic search lets you find journal entries by meaning rather than exact
keywords. For example, searching for "feeling anxious" will also find entries
about "stress" or "worry", even if those exact words weren't used.

### Installation

Semantic search requires an optional dependency:

```sh
poetry install -E semantic
```

### Building the Index

Before searching, build the semantic index. This downloads a small embedding
model (~50 MB) on first run and indexes all your entries:

```sh
alog --index-search
```

### Searching

Use the `-search` flag with a natural language query:

```sh
alog -search "outdoor adventures"
alog -search "cooking recipes"
alog -search "feeling happy"
```

Results are ranked by relevance. You can combine `-search` with other
filters:

```sh
alog -search "travel" -from 2025
alog -search "work stress" -n 5
```

### Auto-Indexing

By default, you need to run `--index-search` manually to update the index
after adding entries. To index automatically on every write, set `auto_index`
to `true` in your [configuration file](./reference-config-file.md#semantic_search):

```yaml
semantic_search:
  auto_index: true
```

### Encrypted Journals

Semantic search works with encrypted journals. The semantic index is encrypted
with a separate key derived from your journal password, so embeddings are never
stored in plain text.
