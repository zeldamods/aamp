# Copyright 2018 leoetlino <leo@leolam.fr>
# Licensed under GPLv2+
from collections import deque, defaultdict
from enum import IntFlag
import io
import typing
import zlib

from aamp.parameters import *
from aamp.util import *

class HeaderFlags(IntFlag):
    LittleEndian = 1 << 0
    UTF8 = 1 << 1

class Reader:
    def __init__(self, data: bytes, track_strings: bool = False) -> None:
        self._data = data
        self._crc32_to_string_map: typing.Dict[int, str] = dict()
        self._track_strings = track_strings

        magic = self._data[0:4]
        if magic != b'AAMP':
            raise ValueError("Invalid magic: %s (expected 'AAMP')" % magic)

        flags = get_u32(self._data, 0x8)
        if (flags & HeaderFlags.LittleEndian) == 0:
            raise ValueError('Only little endian parameter archives are supported')
        if (flags & HeaderFlags.UTF8) == 0:
            raise ValueError('Only UTF-8 parameter archives are supported')

    def parse(self) -> ParameterIO:
        param_io = ParameterIO()
        param_io.type = get_string(self._data, 0x30)
        param_io.version = get_u32(self._data, 0x10)
        format_len = get_u32(self._data, 0x14)
        root_crc32, root_list = self._parse_list(0x30 + format_len)
        param_io.lists[root_crc32] = root_list
        return param_io

    def _parse_list(self, offset: int) -> typing.Tuple[int, ParameterList]:
        param_list = ParameterList()
        crc32 = get_u32(self._data, offset + 0)
        param_list._crc32 = crc32

        obj_offset = offset + 4*get_u16(self._data, offset + 8)
        obj_count = get_u16(self._data, offset + 0xa)
        for i in range(obj_count):
            obj_crc32, obj = self._parse_obj(obj_offset)
            param_list.objects[obj_crc32] = obj
            obj_offset += 8

        list_offset = offset + 4*get_u16(self._data, offset + 4)
        list_count = get_u16(self._data, offset + 6)
        for i in range(list_count):
            list_crc32, plist = self._parse_list(list_offset)
            param_list.lists[list_crc32] = plist
            list_offset += 0xc

        return (crc32, param_list)

    def _parse_obj(self, offset: int) -> typing.Tuple[int, ParameterObject]:
        param_obj = ParameterObject()
        crc32 = get_u32(self._data, offset + 0)
        param_obj._crc32 = crc32

        param_offset = offset + 4*get_u16(self._data, offset + 4)
        param_count = get_u16(self._data, offset + 6)
        for i in range(param_count):
            param_crc32, param = self._parse_param(param_offset)
            param_obj.params[param_crc32] = param
            param_offset += 8

        return (crc32, param_obj)

    def _parse_param_str(self, offset: int, data_offset: int, str_class, max_size: int) -> typing.Any:
        data_size = self._data.find(0, data_offset) - data_offset
        string_len = data_size if max_size == -1 else min(data_size, max_size)
        b = self._data[data_offset:data_offset + string_len]
        s = b.decode()
        if self._track_strings:
            self._register_string(b, s)
        return str_class(s)

    def _parse_param(self, offset: int) -> typing.Tuple[int, typing.Any]:
        crc32 = get_u32(self._data, offset)
        field_4 = get_u32(self._data, offset + 4)
        data_offset = offset + 4 * (field_4 & 0xffffff)
        param_type = field_4 >> 24
        value: typing.Any = None

        if param_type == ParameterType.Bool:
            value = get_u32(self._data, data_offset) != 0

        elif param_type == ParameterType.Vec2:
            value = Vec2(get_f32(self._data, data_offset), get_f32(self._data, data_offset + 4))
        elif param_type == ParameterType.Vec3:
            value = Vec3(get_f32(self._data, data_offset), get_f32(self._data, data_offset + 4), get_f32(self._data, data_offset + 8))
        elif param_type == ParameterType.Vec4:
            value = Vec4(get_f32(self._data, data_offset), get_f32(self._data, data_offset + 4), get_f32(self._data, data_offset + 8), get_f32(self._data, data_offset + 0xc))
        elif param_type == ParameterType.Color:
            value = Color(get_f32(self._data, data_offset), get_f32(self._data, data_offset + 4), get_f32(self._data, data_offset + 8), get_f32(self._data, data_offset + 0xc))

        elif param_type == ParameterType.String32:
            value = self._parse_param_str(offset, data_offset, String32, 32)
        elif param_type == ParameterType.String64:
            value = self._parse_param_str(offset, data_offset, String64, 64)
        elif param_type == ParameterType.String256:
            value = self._parse_param_str(offset, data_offset, String256, 256)
        elif param_type == ParameterType.StringRef:
            value = self._parse_param_str(offset, data_offset, str, -1)

        elif param_type == ParameterType.Curve1 \
        or param_type == ParameterType.Curve2 \
        or param_type == ParameterType.Curve3 \
        or param_type == ParameterType.Curve4:
            num_curves = param_type - ParameterType.Curve1 + 1
            value = Curve()
            for i in range(num_curves):
                value.v.extend(get_u32(self._data, data_offset + 0x80*i + 4*x) for x in range(2))
                value.v.extend(get_f32(self._data, data_offset + 0x80*i + 8 + 4*x) for x in range(30))

        elif param_type == ParameterType.Quat:
            # Quat parameters receive additional processing after being loaded:
            # depending on what parameters are passed to the apply function,
            # there may be linear interpolation going on.
            # We currently ignore all of that stuff.
            value = Quat(*[get_f32(self._data, data_offset + 4*i) for i in range(4)])

        elif param_type == ParameterType.Int:
            value = get_s32(self._data, data_offset)
        elif param_type == ParameterType.BufferInt:
            value = [None] * get_u32(self._data, data_offset - 4)
            for i in range(len(value)):
                value[i] = get_s32(self._data, data_offset + 4*i)

        elif param_type == ParameterType.U32:
            value = U32(get_u32(self._data, data_offset))
        elif param_type == ParameterType.BufferU32:
            value = [None] * get_u32(self._data, data_offset - 4)
            for i in range(len(value)):
                value[i] = U32(get_u32(self._data, data_offset + 4*i))

        elif param_type == ParameterType.F32:
            # There's some trickery going on in the parse function -- floats can
            # in some cases get multiplied by some factor.
            # Though this shouldn't really matter since we target BotW parameter archives.
            value = get_f32(self._data, data_offset)
        elif param_type == ParameterType.BufferF32:
            value = [None] * get_u32(self._data, data_offset - 4)
            for i in range(len(value)):
                value[i] = get_f32(self._data, data_offset + 4*i)

        elif param_type == ParameterType.BufferBinary:
            buffer_size = get_u32(self._data, data_offset - 4)
            value = self._data[data_offset:data_offset + buffer_size]

        else:
            raise ValueError('Unknown parameter type: %u' % param_type)

        return (crc32, value)

    def _register_string(self, b: bytes, s: str) -> None:
        self._crc32_to_string_map[zlib.crc32(b)] = s

class _ListWriteContext(typing.NamedTuple):
    list_offset_writer: PlaceholderOffsetWriter
    obj_offset_writer: PlaceholderOffsetWriter
    plist: ParameterList

class _ObjWriteContext(typing.NamedTuple):
    param_offset_writer: PlaceholderOffsetWriter
    pobj: ParameterObject

class Writer:
    def __init__(self, param_io: ParameterIO) -> None:
        self._pio = param_io
    
    def get_bytes(self) -> bytes:
        stream = io.BytesIO()
        self.write(stream)
        return stream.getvalue()

    def write(self, stream: typing.BinaryIO) -> None:
        self._num_lists = 0
        self._num_objs = 0
        self._num_params = 0
        self._lists: typing.Deque[_ListWriteContext] = deque()
        self._objs: typing.Deque[_ObjWriteContext] = deque()
        self._values: typing.List[typing.Tuple[bytes, typing.List[typing.Tuple[int, PlaceholderOffsetWriter]]]] = list()
        self._strings: typing.DefaultDict[bytes, typing.List[PlaceholderOffsetWriter]] = defaultdict(list)

        # Header
        stream.write(b'AAMP')
        stream.write(u32(2)) # Version
        stream.write(u32(HeaderFlags.LittleEndian | HeaderFlags.UTF8))
        size_writer = self._write_placeholder_u32(stream)
        stream.write(u32(0)) # Padding?
        stream.write(u32(align_up(len(self._pio.type) + 1, 4)))
        num_lists_writer = self._write_placeholder_u32(stream) # including root ParameterIO
        num_objs_writer = self._write_placeholder_u32(stream)
        num_params_writer = self._write_placeholder_u32(stream)
        data_section_size_writer = self._write_placeholder_u32(stream)
        string_section_size_writer = self._write_placeholder_u32(stream)
        stream.write(u32(0)) # Unknown: number of uint32s after the string section

        stream.write(string(self._pio.type))
        stream.seek(align_up(stream.tell(), 4))

        # Write parameter lists recursively, starting from the root list.
        self._write_list(stream, *next(iter(self._pio.lists.items())))
        # Actually write list data now.
        list_contexts = []
        while self._lists:
            list_contexts.append(self._lists.popleft())
            self._write_list_data(stream, list_contexts[-1])
        # While not strictly necessary, write all lists before writing objects
        # to match Nintendo's official binary parameter archive tool and
        # to prevent aamptool from choking on generated AAMPs.
        for ctx in list_contexts:
            ctx.obj_offset_writer.write_offset_16(stream.tell())
            for cobj_crc32, cobj in ctx.plist.objects.items():
                self._write_object(stream, cobj_crc32, cobj)

        while self._objs:
            self._write_object_data(stream, self._objs.popleft())

        data_section_start = stream.tell()
        for v, offsets in self._values:
            for offset, w in offsets:
                w.write_offset_24(stream.tell() + offset)
            stream.write(v)
            stream.seek(align_up(stream.tell(), 4))
        data_section_size_writer.write_offset_32(stream.tell() - data_section_start)

        string_section_start = stream.tell()
        for v, offset_writers in self._strings.items():
            stream.seek(align_up(stream.tell(), 4))
            for w in offset_writers:
                w.write_offset_24(stream.tell())
            stream.write(v)
        stream.write(b'\x00' * (align_up(stream.tell(), 4) - stream.tell()))
        string_section_size_writer.write_offset_32(stream.tell() - string_section_start)

        num_lists_writer.write_offset_32(self._num_lists)
        num_objs_writer.write_offset_32(self._num_objs)
        num_params_writer.write_offset_32(self._num_params)
        size_writer.write_offset_32(stream.tell())

    def _write_list(self, stream: typing.BinaryIO, crc32: int, plist: ParameterList) -> None:
        self._num_lists += 1
        start_offset = stream.tell()
        stream.write(u32(crc32))
        list_offset_writer = self._write_placeholder_u16(stream, base=start_offset)
        stream.write(u16(len(plist.lists)))
        obj_offset_writer = self._write_placeholder_u16(stream, base=start_offset)
        stream.write(u16(len(plist.objects)))
        self._lists.append(_ListWriteContext(list_offset_writer, obj_offset_writer, plist))

    def _write_list_data(self, stream: typing.BinaryIO, ctx: _ListWriteContext) -> None:
        ctx.list_offset_writer.write_offset_16(stream.tell())
        for clist_crc32, clist in ctx.plist.lists.items():
            self._write_list(stream, clist_crc32, clist)

    def _write_object(self, stream: typing.BinaryIO, crc32: int, pobj: ParameterObject) -> None:
        self._num_objs += 1
        start_offset = stream.tell()
        stream.write(u32(crc32))
        param_offset_writer = self._write_placeholder_u16(stream, base=start_offset)
        stream.write(u16(len(pobj.params)))
        self._objs.append(_ObjWriteContext(param_offset_writer, pobj))

    def _write_object_data(self, stream: typing.BinaryIO, ctx: _ObjWriteContext) -> None:
        ctx.param_offset_writer.write_offset_16(stream.tell())
        for param_crc32, param in ctx.pobj.params.items():
            start_offset = stream.tell()
            self._num_params += 1
            param_type, param_bytes = value_to_bytes(param)
            stream.write(u32(param_crc32))
            p = self._write_placeholder_u24(stream, base=start_offset)
            stream.write(u8(param_type))
            if isinstance(param, str):
                self._strings[param_bytes].append(p)
            else:
                found = False
                for v, writers in self._values:
                    try:
                        offset = v.index(param_bytes)
                        writers.append((offset, p))
                        found = True
                        break
                    except ValueError:
                        continue
                if not found:
                    self._values.append((param_bytes, [(0, p)]))

    def _write_placeholder_u32(self, stream: typing.BinaryIO, base: int = 0) -> PlaceholderOffsetWriter:
        p = PlaceholderOffsetWriter(stream, base)
        p.write_placeholder_32()
        return p

    def _write_placeholder_u24(self, stream: typing.BinaryIO, base: int = 0) -> PlaceholderOffsetWriter:
        p = PlaceholderOffsetWriter(stream, base)
        p.write_placeholder_24()
        return p

    def _write_placeholder_u16(self, stream: typing.BinaryIO, base: int = 0) -> PlaceholderOffsetWriter:
        p = PlaceholderOffsetWriter(stream, base)
        p.write_placeholder_16()
        return p
