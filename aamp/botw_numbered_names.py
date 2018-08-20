import os
import typing

numbered_name_list: typing.List[str] = []
with open(os.path.dirname(os.path.realpath(__file__)) + '/botw_numbered_names.txt', 'r', encoding='utf-8') as f:
    numbered_name_list = [l[:-1] for l in f]
