from aamp.parameters import *
from aamp.botw_hashed_names import hash_to_name_map
from aamp.botw_numbered_names import numbered_name_list
import functools
import yaml
import zlib

def represent_float(dumper, value):
    s = f'{value:g}'
    if 'e' not in s and '.' not in s:
        s += '.0'
    return dumper.represent_scalar(u'tag:yaml.org,2002:float', s)

# From PyYAML: https://github.com/yaml/pyyaml/blob/a9c28e0b52/lib3/yaml/representer.py
# with the sorting code removed.
def represent_mapping(dumper, tag, mapping, flow_style=None):
    value = [] # type: ignore
    node = yaml.MappingNode(tag, value, flow_style=flow_style)
    best_style = True
    if hasattr(mapping, 'items'):
        mapping = list(mapping.items())
    for item_key, item_value in mapping:
        node_key = dumper.represent_data(item_key)
        node_value = dumper.represent_data(item_value)
        if not (isinstance(node_key, yaml.ScalarNode) and not node_key.style):
            best_style = False
        if not (isinstance(node_value, yaml.ScalarNode) and not node_value.style):
            best_style = False
        value.append((node_key, node_value))
    if flow_style is None:
        if dumper.default_flow_style is not None:
            node.flow_style = dumper.default_flow_style
        else:
            node.flow_style = best_style
    return node

def represent_dict(dumper, mapping, flow_style=None):
    return represent_mapping(dumper, 'tag:yaml.org,2002:map', mapping, flow_style)

def _fields(data) -> list:
    return [getattr(data, x) for x in data.__slots__]

@functools.lru_cache(maxsize=None)
def _test_possible_numbered_names(idx: int, wanted_hash: int) -> str:
    for nname in numbered_name_list:
        for i in range(idx + 2):
            possible_name = nname % i
            if zlib.crc32(possible_name.encode()) == wanted_hash:
                return possible_name
    return ''

def _get_pstruct_name(reader, idx: int, k: int, parent_crc32: int) -> typing.Union[int, str]:
    name = reader._crc32_to_string_map.get(k, None)
    if name is not None:
        return name

    name = hash_to_name_map.get(k, None)
    if name is not None:
        return name

    # Try to guess the name from the parent parameter list name if possible.
    parent_name = hash_to_name_map.get(parent_crc32, None)
    if parent_name is None:
        nname = _test_possible_numbered_names(idx, k)
        if nname:
            return nname
        return k

    def generate_possible_names(p: str, i: int):
        return (f'{p}{i}', f'{p}_{i}', \
                f'{p}{i:02}', f'{p}_{i:02}', \
                f'{p}{i:03}', f'{p}_{i:03}')

    for i in (idx, idx + 1):
        for possible_name in generate_possible_names(parent_name, i):
            if zlib.crc32(possible_name.encode()) == k:
                return possible_name

    # Sometimes the parent name is plural and the object names are singular.
    if parent_name == 'Children':
        for i in (idx, idx + 1):
            for possible_name in generate_possible_names('Child', i):
                if zlib.crc32(possible_name.encode()) == k:
                    return possible_name
    for suffix in ('s', 'es', 'List'):
        if parent_name.endswith(suffix):
            for i in (idx, idx + 1):
                for possible_name in generate_possible_names(parent_name[:-len(suffix)], i):
                    if zlib.crc32(possible_name.encode()) == k:
                        return possible_name

    nname = _test_possible_numbered_names(idx, k)
    if nname:
        return nname

    # No luck. Use the CRC32 as key.
    return k

def represent_param_object(dumper, pobject: ParameterObject):
    return represent_mapping(dumper, '!obj',
        {_get_pstruct_name(dumper.__aamp_reader, idx, k, pobject._crc32): v for idx, (k, v) in enumerate(pobject.params.items())},
        flow_style=len(pobject.params) <= 4)

def represent_param_list(dumper, plist: ParameterList):
    return represent_mapping(dumper, '!list', {
        'objects': {_get_pstruct_name(dumper.__aamp_reader, idx, k, plist._crc32): v for idx, (k, v) in enumerate(plist.objects.items())},
        'lists': {_get_pstruct_name(dumper.__aamp_reader, idx, k, plist._crc32): v for idx, (k, v) in enumerate(plist.lists.items())},
    }, flow_style=False)

def represent_param_io(dumper, pio: ParameterIO):
    root_list_crc32 = next(iter(pio.lists.keys()))
    return represent_mapping(dumper, '!io', {
        'version': pio.version,
        'type': pio.type,
        hash_to_name_map.get(root_list_crc32, root_list_crc32): next(iter(pio.lists.values())),
    }, flow_style=False)

def _parse_yaml_dict_key(k: typing.Union[int, str]) -> int:
    if isinstance(k, int):
        return k
    return zlib.crc32(k.encode())

def construct_io(d: dict) -> ParameterIO:
    pio = ParameterIO(type_=d['type'], version=d['version'])
    pio.lists = {_parse_yaml_dict_key(k): v for k, v in d.items() if k != 'type' and k != 'version'}
    return pio

def construct_list(d: dict) -> ParameterList:
    plist = ParameterList()
    plist.lists = {_parse_yaml_dict_key(k): v for k, v in d['lists'].items()}
    plist.objects = {_parse_yaml_dict_key(k): v for k, v in d['objects'].items()}
    return plist

def construct_obj(d: dict) -> ParameterObject:
    pobj = ParameterObject()
    pobj.params = {_parse_yaml_dict_key(k): v for k, v in d.items()}
    return pobj

def register_representers(dumper) -> None:
    yaml.add_representer(float, represent_float, Dumper=dumper)
    yaml.add_representer(dict, represent_dict, Dumper=dumper)
    yaml.add_representer(ParameterIO, represent_param_io, Dumper=dumper)
    yaml.add_representer(ParameterList, represent_param_list, Dumper=dumper)
    yaml.add_representer(ParameterObject, represent_param_object, Dumper=dumper)
    yaml.add_representer(Vec2, lambda d, data: d.represent_sequence('!vec2', _fields(data), flow_style=True), Dumper=dumper)
    yaml.add_representer(Vec3, lambda d, data: d.represent_sequence('!vec3', _fields(data), flow_style=True), Dumper=dumper)
    yaml.add_representer(Vec4, lambda d, data: d.represent_sequence('!vec4', _fields(data), flow_style=True), Dumper=dumper)
    yaml.add_representer(Color, lambda d, data: d.represent_sequence('!color', _fields(data), flow_style=True), Dumper=dumper)
    yaml.add_representer(Quat, lambda d, data: d.represent_sequence('!quat', _fields(data), flow_style=True), Dumper=dumper)
    yaml.add_representer(Curve, lambda d, data: d.represent_sequence('!curve', data.v, flow_style=True), Dumper=dumper)
    yaml.add_representer(String32, lambda d, data: d.represent_scalar('!str32', str(data)), Dumper=dumper)
    yaml.add_representer(String64, lambda d, data: d.represent_scalar('!str64', str(data)), Dumper=dumper)
    yaml.add_representer(String256, lambda d, data: d.represent_scalar('!str256', str(data)), Dumper=dumper)
    yaml.add_representer(U32, lambda d, data: d.represent_scalar('!u', str(data)), Dumper=dumper)

def register_constructors(loader) -> None:
    yaml.add_constructor('!io', lambda l, node: construct_io(l.construct_mapping(node, deep=True)), Loader=loader)
    yaml.add_constructor('!list', lambda l, node: construct_list(l.construct_mapping(node, deep=True)), Loader=loader)
    yaml.add_constructor('!obj', lambda l, node: construct_obj(l.construct_mapping(node, deep=True)), Loader=loader)
    yaml.add_constructor('!vec2', lambda l, node: Vec2(*l.construct_sequence(node)), Loader=loader)
    yaml.add_constructor('!vec3', lambda l, node: Vec3(*l.construct_sequence(node)), Loader=loader)
    yaml.add_constructor('!vec4', lambda l, node: Vec4(*l.construct_sequence(node)), Loader=loader)
    yaml.add_constructor('!color', lambda l, node: Color(*l.construct_sequence(node)), Loader=loader)
    yaml.add_constructor('!quat', lambda l, node: Quat(*l.construct_sequence(node)), Loader=loader)
    yaml.add_constructor('!curve', lambda l, node: Curve(*l.construct_sequence(node)), Loader=loader)
    yaml.add_constructor('!str32', lambda l, node: String32(l.construct_yaml_str(node)), Loader=loader)
    yaml.add_constructor('!str64', lambda l, node: String64(l.construct_yaml_str(node)), Loader=loader)
    yaml.add_constructor('!str256', lambda l, node: String256(l.construct_yaml_str(node)), Loader=loader)
    yaml.add_constructor('!u', lambda l, node: U32(l.construct_yaml_int(node)), Loader=loader)
