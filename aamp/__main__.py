#!/usr/bin/env python3
import argparse
import io
import os
import sys
import typing
import yaml

import aamp
import aamp.converters

def do_aamp_to_yml(input_data: bytes, output: typing.BinaryIO) -> None:
    output.write(aamp.converters.aamp_to_yml(input_data))

def do_yml_to_aamp(input_data: bytes, output: typing.BinaryIO) -> None:
    output.write(aamp.converters.yml_to_aamp(input_data))

def main() -> None:
    parser = argparse.ArgumentParser(description='Converts Nintendo parameter archives (AAMP) to a binary or YAML form')
    parser.add_argument('source', help='Path to a YAML or AAMP file')
    parser.add_argument('destination', help='Path to destination (if source file was YAML, it will be converted to AAMP and vice versa)', nargs='?', default='-')
    args = parser.parse_args()

    src: str = args.source
    dst: str = args.destination

    with sys.stdin.buffer if src == '-' else open(src, 'rb') as file:
        input_data = file.read()

    if src != '-':
        dst = dst.replace('!!', os.path.splitext(src)[0])
    elif '!!' in dst:
        sys.stderr.write('error: cannot use !! (for input filename) when reading from stdin\n')
        sys.exit(1)

    output = sys.stdout.buffer if dst == '-' else open(dst, 'wb')
    if len(input_data) <= 0x30 or input_data[0:8] != b'AAMP\x02\x00\x00\x00':
        do_yml_to_aamp(input_data, output)
    else:
        do_aamp_to_yml(input_data, output)

if __name__ == '__main__':
    main()
