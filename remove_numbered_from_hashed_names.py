#!/usr/bin/env python3
from aamp.botw_numbered_names import numbered_name_list
import sys
import typing

blacklist: typing.Set[str] = set()
for nname in numbered_name_list:
    for i in range(1000 + 1):
        blacklist.add(nname % i)

with open(sys.argv[1], 'r', encoding='utf-8') as f:
    for l in f:
        sl = l.rstrip('\n')
        if sl not in blacklist:
            print(sl)
