import os
import typing
import zlib

hash_to_name_map: typing.Dict[int, str] = dict()
with open(os.path.dirname(os.path.realpath(__file__)) + '/botw_hashed_names.txt', 'r', encoding='utf-8') as f:
    hash_to_name_map = {zlib.crc32(l[:-1].encode()): l[:-1] for l in f}
