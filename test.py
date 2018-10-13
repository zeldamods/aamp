#!/usr/bin/env python3
import os
from pathlib import Path
import subprocess
import sys

def run_aamp(data: bytes) -> bytes:
    return subprocess.run(['aamp', '-'], input=data,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout

for path in Path(os.path.dirname(os.path.realpath(__file__))).glob('test_data/*.b*'):
    print(path.name)

    aamp_data = path.open('rb').read()
    yml_data = run_aamp(aamp_data)
    reconverted_aamp_data = run_aamp(yml_data)
    if reconverted_aamp_data != aamp_data:
        sys.stderr.write(f'  WARN: {path.name} is different from original\n')
    if run_aamp(reconverted_aamp_data) != yml_data:
        sys.stderr.write(f'  FAIL: roundtrip conversion test failed for {path.name}\n')
        sys.exit(1)
