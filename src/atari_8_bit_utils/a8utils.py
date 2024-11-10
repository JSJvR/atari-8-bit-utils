import os
import typer
import logging
from .atascii import to_utf8, to_atascii, files_to_utf8, files_to_atascii
from typing import Callable
from typing_extensions import Annotated
from pathlib import Path
from enum import Enum
import sys

logger = logging.getLogger(__name__)

app = typer.Typer()

class PathType(Enum):
    STDIO = 1
    FILE = 2
    DIR = 3
    ERROR = 4

def path_type(path: str, new_ok: bool=False):
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
        raise typer.BadParameter(f'{input} is not a valid input path')
    if otype == PathType.ERROR:
        raise typer.BadParameter(f'{output} is not a valid output path')

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
            raise typer.BadParameter(f'When input is STDIN, output can\'t be a directory')
        else:
            file_converter(input, output)
    else:
        if otype != PathType.DIR:
            raise typer.BadParameter(f'When input is as directory, output must be a directory')
        else:
            dir_converter(input, output)

@app.command(help="Converts a single file or all files in a directory from ATASCII to UTF-9")
def ata2utf8(
    input: Annotated[str, typer.Argument(help='Input file or directory. Use "-" for STDIN', )] = '-',
    output: Annotated[str, typer.Argument(help='Output file or directory. Use "-" for STDOUT')] = '-'
):
    convert(input, output, to_utf8, files_to_utf8)

@app.command(help="Converts a single file or all files in a directory from UTF-9 to ATASCII")
def utf82ata(
    input: Annotated[str, typer.Argument(help='Input file or directory. Use "-" for STDIN', )] = '-',
    output: Annotated[str, typer.Argument(help='Output file or directory. Use "-" for STDOUT')] = '-'
):
    convert(input, output, to_atascii, files_to_atascii)

if __name__ == "__main__":
    logging.basicConfig(stream=logging.StreamHandler(sys.stdout).stream, level=logging.INFO)
    app()    