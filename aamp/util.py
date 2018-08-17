import struct
import typing

_NUL_CHAR = b'\x00'

def align_up(n: int, align: int) -> int:
    return (n + align - 1) & -align

def u8(value: int) -> bytes:
    return struct.pack('B', value)
def u16(value: int) -> bytes:
    return struct.pack('<H', value)
def u32(value: int) -> bytes:
    return struct.pack('<I', value)
def s32(value: int) -> bytes:
    return struct.pack('<i', value)
def f32(value: float) -> bytes:
    return struct.pack('<f', value)
def string(value: str) -> bytes:
    return value.encode() + _NUL_CHAR

def get_u8(data, offset: int) -> int:
    return struct.unpack_from('B', data, offset)[0]
def get_u16(data, offset: int) -> int:
    return struct.unpack_from('<H', data, offset)[0]
def get_u32(data, offset: int) -> int:
    return struct.unpack_from('<I', data, offset)[0]
def get_s32(data, offset: int) -> int:
    return struct.unpack_from('<i', data, offset)[0]
def get_f32(data, offset: int) -> int:
    return struct.unpack_from('<f', data, offset)[0]
def get_string(data, offset: int) -> str:
    end = data.find(_NUL_CHAR, offset)
    return data[offset:end].decode('utf-8')

class PlaceholderOffsetWriter:
    """Writes a placeholder offset value that will be filled later."""
    def __init__(self, stream: typing.BinaryIO, base: int = 0) -> None:
        self._stream = stream
        self._offset = stream.tell()
        self._base = base

    def write_placeholder_32(self) -> None:
        self._stream.write(u32(0xffffffff))
    def write_placeholder_24(self) -> None:
        self._stream.write(u8(0xff) + u8(0xff) + u8(0xff))
    def write_placeholder_16(self) -> None:
        self._stream.write(u16(0xffff))

    def write_offset_32(self, offset: int) -> None:
        current_offset = self._stream.tell()
        self._stream.seek(self._offset)
        self._stream.write(u32(offset - self._base))
        self._stream.seek(current_offset)

    def write_offset_24(self, offset: int) -> None:
        current_offset = self._stream.tell()
        self._stream.seek(self._offset)
        x = struct.unpack('<I', self._stream.read(4))[0] >> 24
        self._stream.seek(self._offset)
        self._stream.write(u32((x << 24) | ((offset - self._base) >> 2)))
        self._stream.seek(current_offset)

    def write_offset_16(self, offset: int) -> None:
        current_offset = self._stream.tell()
        self._stream.seek(self._offset)
        self._stream.write(u16((offset - self._base) >> 2))
        self._stream.seek(current_offset)
