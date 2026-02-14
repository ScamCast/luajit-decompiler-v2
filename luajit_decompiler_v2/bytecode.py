from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
import struct

from .opcodes import Op, map_opcode, ABC_FORMAT, UNSUPPORTED

BC_HEADER = b"\x1bLJ"
BC_VERSION_1 = 1
BC_VERSION_2 = 2
BC_F_BE = 0x01
BC_F_STRIP = 0x02
BC_F_FFI = 0x04
BC_F_FR2 = 0x08
BC_PROTO_CHILD = 0x01
BC_PROTO_VARARG = 0x02
BC_PROTO_FFI = 0x04


class ParseError(RuntimeError):
    pass


class KTab(IntEnum):
    NIL = 0
    FALSE = 1
    TRUE = 2
    INT = 3
    NUM = 4
    STR = 5


class KGc(IntEnum):
    CHILD = 0
    TAB = 1
    I64 = 2
    U64 = 3
    COMPLEX = 4
    STR = 5


class KNum(IntEnum):
    INT = 0
    NUM = 1


@dataclass
class Instruction:
    op: Op
    a: int
    b: int = 0
    c: int = 0
    d: int = 0


@dataclass
class TableConstant:
    type: KTab
    integer: int | None = None
    number: int | None = None
    string: str = ""


@dataclass
class TableNode:
    key: TableConstant
    value: TableConstant


@dataclass
class Constant:
    type: KGc
    prototype: Prototype | None = None
    array: list[TableConstant] = field(default_factory=list)
    table: list[TableNode] = field(default_factory=list)
    cdata: int = 0
    string: str = ""


@dataclass
class NumberConstant:
    type: KNum
    integer: int | None = None
    number: int | None = None


@dataclass
class ProtoHeader:
    flags: int = 0
    parameters: int = 0
    framesize: int = 0
    has_debug_info: bool = False
    first_line: int = 0
    line_count: int = 0


@dataclass
class Prototype:
    bytecode: Bytecode
    header: ProtoHeader = field(default_factory=ProtoHeader)
    instructions: list[Instruction] = field(default_factory=list)
    upvalues: list[int] = field(default_factory=list)
    constants: list[Constant] = field(default_factory=list)
    number_constants: list[NumberConstant] = field(default_factory=list)
    line_map: list[int] = field(default_factory=list)
    upvalue_names: list[str] = field(default_factory=list)
    variable_infos: list[tuple[str, int, int, bool]] = field(default_factory=list)
    prototype_size: int = 0

    def parse(self, block: bytes, unlinked: list[Prototype]) -> None:
        self._block = block
        self.prototype_size = 0
        self.read_header()
        self.read_instructions()
        self.read_upvalues()
        self.read_constants(unlinked)
        self.read_number_constants()
        self.read_debug_info()
        if self.prototype_size != len(self._block):
            raise ParseError("Prototype has unread bytes left")
        unlinked.append(self)

    def _next(self) -> int:
        if self.prototype_size >= len(self._block):
            raise ParseError("Prototype read exceeds block")
        b = self._block[self.prototype_size]
        self.prototype_size += 1
        return b

    def _uleb128(self) -> int:
        u = self._next()
        if u >= 0x80:
            u &= 0x7F
            shift = 0
            while True:
                shift += 7
                b = self._next()
                u |= (b & 0x7F) << shift
                if b < 0x80:
                    break
        return u

    def _uleb128_33(self) -> int:
        u = self._next() >> 1
        if u >= 0x40:
            u &= 0x3F
            shift = -1
            while True:
                shift += 7
                b = self._next()
                u |= (b & 0x7F) << shift
                if b < 0x80:
                    break
        return u

    def _cstring(self) -> str:
        out = bytearray()
        while True:
            b = self._next()
            if b == 0:
                return out.decode("utf-8", errors="replace")
            out.append(b)

    def read_header(self) -> None:
        h = self.header
        h.flags = self._next()
        if h.flags & ~(BC_PROTO_CHILD | BC_PROTO_VARARG | BC_PROTO_FFI):
            raise ParseError("Prototype has invalid flags")
        h.parameters = self._next()
        h.framesize = self._next()
        self.upvalues = [0] * self._next()
        self.constants = [None] * self._uleb128()  # type: ignore[list-item]
        self.number_constants = [None] * self._uleb128()  # type: ignore[list-item]
        self.instructions = [None] * self._uleb128()  # type: ignore[list-item]
        if not self.instructions:
            raise ParseError("Prototype has no instructions")
        if self.bytecode.flags & BC_F_STRIP:
            return
        if self._uleb128() == 0:
            return
        h.has_debug_info = True
        h.first_line = self._uleb128()
        h.line_count = self._uleb128()

    def read_instructions(self) -> None:
        for i in range(len(self.instructions)):
            op = map_opcode(self._next(), self.bytecode.version)
            if op in UNSUPPORTED:
                raise ParseError(f"Unsupported instruction: {op.name}")
            a = self._next()
            if op in ABC_FORMAT:
                c = self._next()
                b = self._next()
                self.instructions[i] = Instruction(op=op, a=a, b=b, c=c)
            else:
                d = self._next() | (self._next() << 8)
                self.instructions[i] = Instruction(op=op, a=a, d=d)

    def read_upvalues(self) -> None:
        for i in range(len(self.upvalues)):
            self.upvalues[i] = self._next() | (self._next() << 8)

    def _table_constant(self) -> TableConstant:
        t = self._uleb128()
        if t in (KTab.NIL, KTab.FALSE, KTab.TRUE):
            return TableConstant(type=KTab(t))
        if t == KTab.INT:
            return TableConstant(type=KTab.INT, integer=self._uleb128())
        if t == KTab.NUM:
            lo = self._uleb128()
            hi = self._uleb128()
            return TableConstant(type=KTab.NUM, number=lo | (hi << 32))
        strlen = t - KGc.STR
        s = bytes(self._next() for _ in range(strlen)).decode("utf-8", errors="replace")
        return TableConstant(type=KTab.STR, string=s)

    def read_constants(self, unlinked: list[Prototype]) -> None:
        for i in range(len(self.constants)):
            t = self._uleb128()
            if t == KGc.CHILD:
                if not unlinked:
                    raise ParseError("Failed to link child prototype")
                self.constants[i] = Constant(type=KGc.CHILD, prototype=unlinked.pop())
            elif t == KGc.TAB:
                array = [self._table_constant() for _ in range(self._uleb128())]
                table = [TableNode(key=self._table_constant(), value=self._table_constant()) for _ in range(self._uleb128())]
                self.constants[i] = Constant(type=KGc.TAB, array=array, table=table)
            elif t in (KGc.I64, KGc.U64, KGc.COMPLEX):
                if t == KGc.COMPLEX and (self._uleb128() != 0 or self._uleb128() != 0):
                    raise ParseError("Invalid complex cdata")
                lo = self._uleb128()
                hi = self._uleb128()
                self.constants[i] = Constant(type=KGc(t), cdata=lo | (hi << 32))
            else:
                strlen = t - KGc.STR
                s = bytes(self._next() for _ in range(strlen)).decode("utf-8", errors="replace")
                self.constants[i] = Constant(type=KGc.STR, string=s)

    def read_number_constants(self) -> None:
        for i in range(len(self.number_constants)):
            if self._block[self.prototype_size] & 1:
                lo = self._uleb128_33()
                hi = self._uleb128()
                self.number_constants[i] = NumberConstant(type=KNum.NUM, number=lo | (hi << 32))
            else:
                self.number_constants[i] = NumberConstant(type=KNum.INT, integer=self._uleb128_33())

    def read_debug_info(self) -> None:
        if not self.header.has_debug_info:
            return
        count = len(self.instructions)
        if self.header.line_count < 256:
            self.line_map = [self._next() for _ in range(count)]
        elif self.header.line_count < 65536:
            self.line_map = [self._next() | (self._next() << 8) for _ in range(count)]
        else:
            self.line_map = [self._next() | (self._next() << 8) | (self._next() << 16) | (self._next() << 24) for _ in range(count)]
        self.upvalue_names = [self._cstring() for _ in self.upvalues]
        scope_offset = 0
        parameter_count = 0
        while True:
            b = self._next()
            if b == 0:
                break
            if b >= 7:
                name = bytes([b]).decode("latin1") + self._cstring()
            else:
                name = f"<var:{b}>"
            scope_offset += self._uleb128()
            if scope_offset == 1:
                raise ParseError("Variable has invalid scope")
            if scope_offset == 0:
                parameter_count += 1
                end = self._uleb128() - 2
                self.variable_infos.append((name, 0, end, True))
            else:
                begin = scope_offset - 2
                end = begin + self._uleb128()
                self.variable_infos.append((name, begin, end, False))
        if parameter_count != self.header.parameters:
            raise ParseError("Parameter count does not match debug info")


@dataclass
class Bytecode:
    file_path: str
    version: int = 0
    flags: int = 0
    chunkname: str = ""
    prototypes: list[Prototype] = field(default_factory=list)
    main: Prototype | None = None

    def parse(self) -> None:
        raw = Path(self.file_path).read_bytes()
        if len(raw) < 18:
            raise ParseError("File is too small or empty")
        idx = 0
        if raw[:3] != BC_HEADER:
            raise ParseError("Invalid LuaJIT bytecode header")
        idx = 3
        self.version = raw[idx]
        idx += 1
        if self.version not in (BC_VERSION_1, BC_VERSION_2):
            raise ParseError("Unsupported bytecode version")
        self.flags = raw[idx]
        idx += 1
        if self.flags & BC_F_BE:
            raise ParseError("Big-endian bytecode is not supported")

        def read_uleb(data: bytes, start: int) -> tuple[int, int]:
            val = data[start]
            start += 1
            if val >= 0x80:
                val &= 0x7F
                shift = 0
                while True:
                    shift += 7
                    b = data[start]
                    start += 1
                    val |= (b & 0x7F) << shift
                    if b < 0x80:
                        return val, start
            return val, start

        if not (self.flags & BC_F_STRIP):
            size, idx = read_uleb(raw, idx)
            self.chunkname = raw[idx: idx + size].decode("utf-8", errors="replace")
            idx += size

        unlinked: list[Prototype] = []
        while True:
            block_size, idx = read_uleb(raw, idx)
            if block_size == 0:
                break
            block = raw[idx: idx + block_size]
            idx += block_size
            p = Prototype(self)
            p.parse(block, unlinked)
            self.prototypes.append(p)

        if idx != len(raw):
            raise ParseError("Unexpected data after last prototype")
        if len(unlinked) != 1:
            raise ParseError("Failed to link main prototype")
        self.main = unlinked[0]


def bits_to_double(bits: int) -> float:
    return struct.unpack("<d", struct.pack("<Q", bits))[0]
