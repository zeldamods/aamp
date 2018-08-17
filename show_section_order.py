# Debug tool to show section order in a binary parameter archive (AAMP).
from aamp.botw_hashed_names import hash_to_name_map
import struct
import sys
import zlib

for i in range(1000):
    s = f'AI_{i}'
    hash_to_name_map[zlib.crc32(s.encode())] = s
for i in range(1000):
    s = f'Action_{i}'
    hash_to_name_map[zlib.crc32(s.encode())] = s

with open(sys.argv[1], 'rb') as f:
    while True:
        data = f.read(4)
        if len(data) < 4:
            break
        word: int = struct.unpack('<I', data)[0]
        name = hash_to_name_map.get(word, None)
        if name is not None:
            print(f'{name} @ 0x{f.tell():x}')

