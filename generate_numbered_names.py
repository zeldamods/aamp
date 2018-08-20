#!/usr/bin/env python3
import sys

with open(sys.argv[1], 'r') as f:
    for line in f:
        l = line.rstrip('\n')
        if l.count('%') != 1:
            continue
        if '%d' not in l and '%u' not in l and all(f'%0{w}d' not in l for w in range(0, 6)) and all(f'%0{w}u' not in l for w in range(0, 6)):
            continue
        print(l)
