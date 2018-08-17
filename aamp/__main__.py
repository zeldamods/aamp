#!/usr/bin/env python3
import argparse
import io
import os
import shutil
import sys
import yaml

import aamp
import aamp.yaml_util as yu

def aamp_to_yml() -> None:
    parser = argparse.ArgumentParser(description='Converts a parameter archive to YAML.')
    parser.add_argument('aamp', help='Path to a parameter archive (AAMP) file', nargs='?', default='-')
    parser.add_argument('yml', help='Path to destination YAML file', nargs='?', default='-')
    args = parser.parse_args()

    dumper = yaml.CDumper
    yu.register_representers(dumper)

    file = sys.stdin.buffer if args.aamp == '-' else open(args.aamp, 'rb')
    with file:
        reader = aamp.Reader(file.read())
        root = reader.parse()

        if args.aamp != '-':
            args.yml = args.yml.replace('!!', os.path.splitext(args.aamp)[0])
        elif '!!' in args.yml:
            sys.stderr.write('error: cannot use !! (for input filename) when reading from stdin\n')
            sys.exit(1)
        output = sys.stdout if args.yml == '-' else open(args.yml, 'w', encoding='utf-8')
        with output:
            dumper.__aamp_reader = reader
            yaml.dump(root, output, Dumper=dumper, allow_unicode=True, encoding='utf-8')

def yml_to_aamp() -> None:
    parser = argparse.ArgumentParser(description='Converts a YAML file to a parameter archive (AAMP).')
    parser.add_argument('yml', help='Path to a YAML file', nargs='?', default='-')
    parser.add_argument('aamp', help='Path to destination AAMP file', nargs='?', default='-')
    args = parser.parse_args()

    loader = yaml.CSafeLoader
    yu.register_constructors(loader)

    file = sys.stdin if args.yml == '-' else open(args.yml, 'r', encoding='utf-8')
    with file:
        root = yaml.load(file, Loader=loader)
        buf = io.BytesIO()
        aamp.Writer(root).write(buf)
        buf.seek(0)

        if args.yml != '-':
            args.aamp = args.aamp.replace('!!', os.path.splitext(args.yml)[0])
        elif '!!' in args.aamp:
            sys.stderr.write('error: cannot use !! (for input filename) when reading from stdin\n')
            sys.exit(1)

        output = sys.stdout.buffer if args.aamp == '-' else open(args.aamp, 'wb')
        with output:
            shutil.copyfileobj(buf, output)
