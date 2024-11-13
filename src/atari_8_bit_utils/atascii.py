from __future__ import annotations
import os
import sys
from typing import Callable

# Initialize ATASCII to UTF-8 mapping

translate = {
    0x00: '\u2665',
    0x01: '\u251c',
    0x02: '\U0001fb87',
    0x03: '\u2518',
    0x04: '\u2524',
    0x05: '\u2510',
    0x06: '\u2571',
    0x07: '\u2572',
    0x08: '\u25e2',
    0x09: '\u2597',
    0x0a: '\u25e3',
    0x0b: '\u259d',
    0x0c: '\u2598',
    0x0d: '\U0001fb82',
    0x0e: '\u2582',
    0x0f: '\u2596',
    0x10: '\u2663',
    0x11: '\u250c',
    0x12: '\u2500',
    0x13: '\u253c',
    0x14: '\u25cf',
    0x15: '\u2584',
    0x16: '\u258e',
    0x17: '\u252c',
    0x18: '\u2534',
    0x19: '\u258c',
    0x1a: '\u2514',
    0x1b: '\u241b',
    0x1c: '\u2191',
    0x1d: '\u2193',
    0x1e: '\u2190',
    0x1f: '\u2192',
    0x60: '\u2666',
    0x7b: '\u2660',
    0x7c: '\u2502',
    0x7d: '\u21b0',
    0x7e: '\u25c0',
    0x7f: '\u25b6',
    0x82: '\u258a',
    0x88: '\u25e4',
    0x89: '\u259b',
    0x8a: '\u25e5',
    0x8b: '\u2599',
    0x8c: '\u259f',
    0x8d: '\u2586',
    0x8e: '\U0001fb85',
    0x8f: '\u259c',
    0x94: '\u25d8',
    0x95: '\u2580',
    0x96: '\U0001fb8a',
    0x99: '\u2590',
    0x9b: '\n',
    0xa0: '\u2588',
}

# Fill in the characters where the UTF-8 and ATASCII representations are the same
for i in range(0x0, 0x80):
    val = translate.get(i)
    if val is None:
        translate[i] = chr(i)

# Most reverse characters don't have a unicode representation, so for
# those we escape them with a '`'
for i in range(0x80, 0x100):
    val = translate.get(i)
    if val is None:
        val = '`' + translate[i ^ 0x80]
        translate[i] = val


# Initialize UTF-8 to ATASCII mapping
inv_translate = {v: k for k, v in translate.items()}

# Make the '`' escape work for any reverse character
for k, v in translate.items():
    if (not v.startswith('`')) and (inv_translate.get('`' + v) is None):
        inv_translate['`' + v] = k ^ 0x80


# Converts a single file from ATASCII to UTF-8
def to_utf8(in_filename='-', out_filename='-'):
    if in_filename != '-':
        ifile = open(in_filename, 'rb')
    else:
        ifile = sys.stdin

    if out_filename != '-':
        ofile = open(out_filename, 'w', encoding='utf-8')
    else:
        ofile = sys.stdout

    data = ifile.read(1)
    while data:
        c = data[0]
        char = translate[c]
        # print(char, end='')
        ofile.write(char)
        data = ifile.read(1)

    ofile.close()
    ifile.close()


def apply_to_dirs(ipath: str, opath: str, applier: Callable[[str, str], None]):
    # Switch to fully qualified paths
    ipath = os.path.abspath(ipath)
    opath = os.path.abspath(opath)

    # print(f'{ipath} --> {opath}')
    for root, dirs, files in os.walk(ipath):
        outroot = root.replace(ipath, opath)
        # print(f'\tDir {root} --> {outroot}')
        for dirname in dirs:
            dirpath = os.path.join(outroot, dirname)
            if not os.path.exists(dirpath) and not dirname.startswith('.'):
                # print(f'Creating {dirpath}')
                os.mkdir(dirpath)
        for filename in files:
            if not filename.startswith('.'):
                out_filename = os.path.join(outroot, filename)
                in_filename = os.path.join(root, filename)
                # print(f'\tFile: {in_filename} --> {out_filename}')
                applier(in_filename, out_filename)


def files_to_utf8(ipath, opath, clobber=False):
    """
    Recursively converts all files in directory ipath from ATASCII to UTF-8 
    and writes the output to opath
    """
    if clobber:
        clear_dir(opath)

    apply_to_dirs(ipath, opath, to_utf8)


# Converts a single file from UTF-8 to ATASCII
def to_atascii(in_filename='-', out_filename='-'):
    if in_filename != '-':
        ifile = open(in_filename, 'r', encoding='utf-8')
    else:
        ifile = sys.stdin

    if out_filename != '-':
        ofile = open(out_filename, 'wb')
    else:
        ofile = sys.stdout

    data = ifile.read(1)
    while data:
        key = data[0]
        if key == '`':
            key += ifile.read(1)[0]

        byte = inv_translate[key]
        ofile.write(byte.to_bytes(1, 'big'))
        data = ifile.read(1)
    ifile.close()
    ofile.close()


def files_to_atascii(ipath: str, opath: str, clobber: bool = False):
    """
    Recursively converts all files in directory ipath from UTF-8 to ATASCII
    and writes the output to opath
    """
    if clobber:
        clear_dir(opath)
    apply_to_dirs(ipath, opath, to_atascii)


def clear_dir(path):
    """
    Recursively deletes all files and directories in path,
    excluding ones whose name starts with '.'
    """
    print(f'Deleting all files in {path}')
    for root, dirs, files in os.walk(path, topdown=False):
        for filename in files:
            if not filename.startswith('.'):
                os.remove(os.path.join(root, filename))
        for dirname in dirs:
            if not dirname.startswith('.'):
                os.rmdir(os.path.join(root, dirname))


def dump_mappings():
    print('*****************************')
    print('* ATASCII to UTF-8 mappings *')
    print('*****************************')
    for i in range(0x0, 0x100):
        print(hex(i), ': ', translate[i])

    print('\n\n*****************************')
    print('* UTF-8 to ATASCII mappings *')
    print('*****************************')
    for k, v in inv_translate.items():
        print(k, ': ', hex(v))


if __name__ == '__main__':
    dump_mappings()
