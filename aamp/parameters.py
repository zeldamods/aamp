import abc
from dataclasses import dataclass, field
from enum import IntEnum
import typing
import zlib

from aamp.util import *

class ParameterType(IntEnum):
    Bool = 0
    F32 = 1
    Int = 2
    Vec2 = 3 # sead::Vector2<float>
    Vec3 = 4 # sead::Vector3<float>
    Vec4 = 5 # sead::Vector4<float>
    Color = 6 # sead::Color4f
    String32 = 7
    String64 = 8
    Curve1 = 9
    Curve2 = 10
    Curve3 = 11
    Curve4 = 12
    BufferInt = 13 # int*
    BufferF32 = 14 # float*
    String256 = 15
    Quat = 16 # sead::Quat<float>
    U32 = 17
    BufferU32 = 18 # unsigned int*
    BufferBinary = 19 # unsigned char*
    StringRef = 20 # sead::SafeString

class ParameterObject:
    __slots__ = ('params', '_crc32')
    def __init__(self) -> None:
        self.params: typing.Dict[int, typing.Any] = dict()
        self._crc32 = -1

    def param(self, name: str):
        return self.params[zlib.crc32(name.encode())]

    def set_param(self, name: str, v) -> None:
        """Add or update an existing parameter."""
        self.params[zlib.crc32(name.encode())] = v

    def __repr__(self) -> str:
        return f'ParameterObject(params={repr(self.params)})'

class ParameterList:
    __slots__ = ('objects', 'lists', '_crc32')
    def __init__(self) -> None:
        self.objects: typing.Dict[int, ParameterObject] = dict()
        self.lists: typing.Dict[int, ParameterList] = dict()
        self._crc32 = -1

    def object(self, name: str) -> ParameterObject:
        return self.objects[zlib.crc32(name.encode())]

    def list(self, name: str):
        return self.lists[zlib.crc32(name.encode())]

    def set_object(self, name: str, pobj: ParameterObject) -> None:
        """Add or update an existing object."""
        self.objects[zlib.crc32(name.encode())] = pobj

    def set_list(self, name: str, plist) -> None:
        """Add or update an existing list."""
        self.lists[zlib.crc32(name.encode())] = plist

    def __repr__(self) -> str:
        return f'ParameterList(objects={repr(self.objects)}, lists={repr(self.lists)})'

class ParameterIO(ParameterList):
    __slots__ = ('version', 'type')
    def __init__(self, type_: str='xml', version=0) -> None:
        super().__init__()
        self.version = version
        self.type = type_
    def __repr__(self) -> str:
        return f'ParameterIO(type_={self.type}, version={self.version}, lists={repr(self.lists)})'

@dataclass
class Vec2:
    x: float = 0.0
    y: float = 0.0

@dataclass
class Vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

@dataclass
class Vec4:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 0.0

@dataclass
class Color:
    r: float = 0.0
    g: float = 0.0
    b: float = 0.0
    a: float = 0.0

class String32(str):
    def __repr__(self) -> str:
        return f'String32({self})'

class String64(str):
    def __repr__(self) -> str:
        return f'String64({self})'

class String256(str):
    def __repr__(self) -> str:
        return f'String256({self})'

class U32(int):
    pass

@dataclass
class Quat:
    a: float = 0.0
    b: float = 0.0
    c: float = 0.0
    d: float = 0.0

@dataclass
class Curve:
    v: list = field(default_factory=list)

def value_to_bytes(v: typing.Any) -> typing.Tuple[ParameterType, bytes]:
    if isinstance(v, bool):
        return (ParameterType.Bool, u32(v))
    if isinstance(v, float):
        return (ParameterType.F32, f32(v))
    if isinstance(v, U32):
        return (ParameterType.U32, u32(v))
    if isinstance(v, int):
        return (ParameterType.Int, s32(v))
    if isinstance(v, Vec2):
        return (ParameterType.Vec2, f32(v.x) + f32(v.y))
    if isinstance(v, Vec3):
        return (ParameterType.Vec3, f32(v.x) + f32(v.y) + f32(v.z))
    if isinstance(v, Vec4):
        return (ParameterType.Vec4, f32(v.x) + f32(v.y) + f32(v.z) + f32(v.w))
    if isinstance(v, Color):
        return (ParameterType.Color, f32(v.r) + f32(v.g) + f32(v.b) + f32(v.a))
    if isinstance(v, Quat):
        return (ParameterType.Quat, f32(v.a) + f32(v.b) + f32(v.c) + f32(v.d))
    if isinstance(v, Curve):
        buf = b''
        for item in v.v:
            if isinstance(item, int):
                buf += u32(item)
            elif isinstance(item, float):
                buf += f32(item)
            else:
                raise ValueError('Invalid item in curve parameter')
        return (ParameterType(ParameterType.Curve1 + (len(buf) // 0x80) - 1), buf)
    if isinstance(v, String32):
        return (ParameterType.String32, string(v))
    if isinstance(v, String64):
        return (ParameterType.String64, string(v))
    if isinstance(v, String256):
        return (ParameterType.String256, string(v))
    if isinstance(v, str):
        return (ParameterType.StringRef, string(v))
    if isinstance(v, bytes):
        return (ParameterType.BufferBinary, v)
    # if isinstance(v, list):
    #     for i in range(len(v) - 1):
    #         if not isinstance(v[i], type(v[i + 1])):
    #             raise ValueError('Arrays/buffers must have homogeneous types')
    #     if not v:
    #         raise ValueError('Arrays/buffers must not be empty')
    #     if isinstance(v[0], U32):
    #         return (ParameterType.BufferU32, b''.join(u32(x) for x in v))
    #     if isinstance(v[0], int):
    #         return (ParameterType.BufferInt, b''.join(s32(x) for x in v))
    #     if isinstance(v[0], float):
    #         return (ParameterType.BufferF32, b''.join(f32(x) for x in v))
    raise ValueError('Unsupported or invalid data type')
