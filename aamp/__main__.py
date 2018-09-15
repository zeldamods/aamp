#!/usr/bin/env python3
import argparse
import io
import os
import shutil
import sys
import typing
import yaml

import aamp
import aamp.yaml_util as yu

def do_aamp_to_yml(input_data: bytes, output: typing.TextIO) -> None:
    dumper = yaml.CDumper
    yu.register_representers(dumper)
    reader = aamp.Reader(input_data)
    root = reader.parse()
    dumper.__aamp_reader = reader
    yaml.dump(root, output, Dumper=dumper, allow_unicode=True, encoding='utf-8')

def do_yml_to_aamp(input_data: bytes, output: typing.BinaryIO) -> None:
    loader = yaml.CSafeLoader
    yu.register_constructors(loader)

    root = yaml.load(input_data, Loader=loader)
    buf = io.BytesIO()
    aamp.Writer(root).write(buf)
    buf.seek(0)
    shutil.copyfileobj(buf, output)

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

    if len(input_data) <= 0x30 or input_data[0:8] != b'AAMP\x02\x00\x00\x00':
        do_yml_to_aamp(input_data, sys.stdout.buffer if dst == '-' else open(dst, 'wb'))
    else:
        do_aamp_to_yml(input_data, sys.stdout if dst == '-' else open(dst, 'w', encoding='utf-8'))

if __name__ == '__main__':
    main()
