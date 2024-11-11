# Atari 8-bit Python Utilities
![Auto Tag badge](https://github.com/JSJvR/atari-8-bit-utils/actions/workflows/auto_tag.yml/badge.svg) ![Python Package badge](https://github.com/JSJvR/atari-8-bit-utils/actions/workflows/python-package.yml/badge.svg) ![Python Publish badge](https://github.com/JSJvR/atari-8-bit-utils/actions/workflows/python-publish.yml/badge.svg) 

## Prerequisites

- Python 3.8 or later
- Optional: A version of [`mkatr`](https://github.com/dmsc/mkatr) compiled for you platform, in your `PATH`. Needed for `atr2git` command to work. 

## Getting Started

The package can be installed using `pip`

```
pip install atari-8-bit-utils
```

Verify the installation by running `a8utils --help`

The output should look something like this

```
 Usage: a8utils [OPTIONS] COMMAND [ARGS]...

╭─ Options ────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current     │
│                               shell.                                 │
│ --show-completion             Show completion for the current shell, │
│                               to copy it or customize the            │
│                               installation.                          │
│ --help                        Show this message and exit.            │
╰──────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────╮
│ ata2utf    Converts a single file or all files in a directory from   │
│            ATASCII to UTF-8                                          │
│ utf2ata    Converts a single file or all files in a directory from   │
│            UTF-8 to ATASCII                                          │
│ atr2git    Keeps an ATR image and git repo in sync                   │
╰──────────────────────────────────────────────────────────────────────╯
```

## Commands

TODO

## Demo

The best way to make full use of this project is to start with the [Atari 8-bit Git template](https://github.com/JSJvR/atari-8-bit-git-template)

https://github.com/user-attachments/assets/e0558c34-0741-4e70-920e-98a72fade00e

The video shows [this commit](https://github.com/JSJvR/atari-8-bit-git-template/commit/14f69b4393901dea558b4a9ecce9b8b7189de932) being made from my Atari. Note that the [BASIC listing](https://github.com/JSJvR/atari-8-bit-git-template/blob/367d22375184d9a73c7c38c9ff049913a7ef558b/utf8/LOVE.LST) and the commit message both contain a "♥" which is `0x00` in ATASCII and therefore not valid in a standard text file. ATASCII characters get translated automatically to their [closest Unicode equivalent](https://www.kreativekorp.com/charset/map/atascii/).