import os
import typer
import logging
from .atascii import to_utf8, to_atascii, files_to_utf8, files_to_atascii
from .sync import sync_main
from typing import Callable, Optional
from typing_extensions import Annotated
from pathlib import Path
from enum import Enum
from .__about__ import __version__ as version
import sys

logger = logging.getLogger(__name__)

app = typer.Typer()


class PathType(Enum):
    STDIO = 1
    FILE = 2
    DIR = 3
    ERROR = 4


def path_type(path: str, new_ok: bool = False):
    logging.info(f'Path: {path}')
    if (path == '-'):
        return PathType.STDIO
    if not new_ok and not os.path.exists(path):
        return PathType.ERROR
    if os.path.isdir(path) and os.path.exists(path):
        return PathType.DIR
    if new_ok or os.path.isfile(path):
        return PathType.FILE
    else:
        return PathType.ERROR


def convert(input: str, output: str, file_converter: Callable, dir_converter):

    itype = path_type(input)
    otype = path_type(output, True)
    if itype == PathType.ERROR:
        raise typer.BadParameter(f'[INPUT]: {input} is not a valid input path')
    if otype == PathType.ERROR:
        raise typer.BadParameter(f'[OUTPUT]: {output} is not a valid output path')

    logger.info(f'Input: {input}({itype}), Output: {output}({otype})')
    # If the input path is a file and the output path is a directory, use the same filename
    # as the input file.
    if itype == PathType.FILE:
        if otype == PathType.DIR:
            p = Path(input)
            logger.info(f'Using filename {p.name} in output directory {output}')
            output = os.path.join(output, p.name)
        file_converter(input, output)
    elif itype == PathType.STDIO:
        if otype == PathType.DIR:
            raise typer.BadParameter(f'[OUTPUT]: {output}. When [INPUT] is STDIN, [OUTPUT] can\'t be a directory')
        else:
            file_converter(input, output)
    else:
        if otype != PathType.DIR:
            raise typer.BadParameter(f'[INPUT]: {input}. When [INPUT] is as directory, [OUTPUT] must be a directory')
        else:
            dir_converter(input, output)


@app.command(help="Converts a single file or all files in a directory from ATASCII to UTF-8")
def ata2utf(
    input: Annotated[str, typer.Argument(help='Input file or directory. Use "-" for STDIN', )] = '-',
    output: Annotated[str, typer.Argument(help='Output file or directory. Use "-" for STDOUT')] = '-'
):
    convert(input, output, to_utf8, files_to_utf8)


@app.command(help="Converts a single file or all files in a directory from UTF-8 to ATASCII")
def utf2ata(
    input: Annotated[str, typer.Argument(help='Input file or directory. Use "-" for STDIN', )] = '-',
    output: Annotated[str, typer.Argument(help='Output file or directory. Use "-" for STDOUT')] = '-'
):
    convert(input, output, to_atascii, files_to_atascii)


def version_callback(value: bool):
    if value:
        print(f'Atari 8-bit Utils Version {version}')
        sys.exit()


@app.command(help='Keeps an ATR image and git repo in sync')
def atr2git(
    reset_config: Annotated[bool, typer.Option(help='Overwrite existing state.json with default values')] = False,
    once: Annotated[Optional[bool], typer.Option(
        help='Synchronize only once and exit when there is nothing to do.')] = None,
    daemon: Annotated[Optional[bool], typer.Option(
        help='Run forever in a loop. Overrides config.daemon in state.json')] = None,
    out: Annotated[str, typer.Option(
        help='The base directory for changes from your Atari. Must have a "atr" subdirectory that contains your atr file(s). ', callback=version_callback, is_eager=True)] = '.'
):
    sync_main(reset_config, once, daemon)


@app.callback()
def main(version: Annotated[Optional[bool], typer.Option(help='Prints version information and exits', callback=version_callback, is_eager=True)] = None):
    """
    A collection of utilities for manipulating files and disk images for Atari 8-bit computers.

    https://github.com/JSJvR/atari-8-bit-utils/

    https://pypi.org/project/atari-8-bit-utils/
    """


if __name__ == "__main__":
    logging.basicConfig(stream=logging.StreamHandler(sys.stdout).stream, level=logging.INFO)
    app()
