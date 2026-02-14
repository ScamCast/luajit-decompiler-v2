from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .bytecode import Bytecode, Prototype, bits_to_double, KNum, KGc
from .opcodes import Op


@dataclass
class Decompiler:
    bytecode: Bytecode
    ignore_debug_info: bool = False
    minimize_diffs: bool = False

    def decompile(self) -> str:
        if self.bytecode.main is None:
            self.bytecode.parse()
        assert self.bytecode.main is not None
        return self._emit_function(self.bytecode.main, level=0, is_root=True)

    def write(self, output_path: str) -> None:
        Path(output_path).write_text(self.decompile(), encoding="utf-8")

    def _num(self, proto: Prototype, idx: int) -> str:
        n = proto.number_constants[idx]
        if n.type == KNum.INT:
            return str(n.integer)
        return repr(bits_to_double(n.number or 0))

    def _const_str(self, proto: Prototype, idx: int) -> str:
        c = proto.constants[idx]
        if c.type == KGc.STR:
            return repr(c.string)
        if c.type == KGc.TAB:
            return "{}"
        if c.type in (KGc.I64, KGc.U64, KGc.COMPLEX):
            return str(c.cdata)
        return "<proto>"

    def _emit_function(self, proto: Prototype, level: int, is_root: bool = False) -> str:
        ind = "    " * level
        lines: list[str] = []
        if not is_root:
            lines.append(f"{ind}function(...)" if proto.header.flags & 0x02 else f"{ind}function()")
            ind = "    " * (level + 1)

        regs: dict[int, str] = {}
        for pc, ins in enumerate(proto.instructions):
            op = ins.op
            if op == Op.MOV:
                regs[ins.a] = regs.get(ins.d, f"slot{ins.d}")
                lines.append(f"{ind}local slot{ins.a} = {regs[ins.a]}")
            elif op == Op.KSHORT:
                val = ins.d if ins.d < 0x8000 else ins.d - 0x10000
                regs[ins.a] = str(val)
                lines.append(f"{ind}local slot{ins.a} = {val}")
            elif op == Op.KNUM:
                regs[ins.a] = self._num(proto, ins.d)
                lines.append(f"{ind}local slot{ins.a} = {regs[ins.a]}")
            elif op == Op.KSTR:
                regs[ins.a] = self._const_str(proto, ins.d)
                lines.append(f"{ind}local slot{ins.a} = {regs[ins.a]}")
            elif op == Op.KNIL:
                for r in range(ins.a, ins.d + 1):
                    regs[r] = "nil"
                    lines.append(f"{ind}local slot{r} = nil")
            elif op in (Op.ADDVV, Op.SUBVV, Op.MULVV, Op.DIVVV, Op.MODVV, Op.POW):
                operator = {
                    Op.ADDVV: "+", Op.SUBVV: "-", Op.MULVV: "*", Op.DIVVV: "/", Op.MODVV: "%", Op.POW: "^"
                }[op]
                lhs = regs.get(ins.b, f"slot{ins.b}")
                rhs = regs.get(ins.c, f"slot{ins.c}")
                regs[ins.a] = f"({lhs} {operator} {rhs})"
                lines.append(f"{ind}slot{ins.a} = {regs[ins.a]}")
            elif op == Op.CALL:
                fn = regs.get(ins.a, f"slot{ins.a}")
                args = ", ".join(regs.get(ins.a + i, f"slot{ins.a + i}") for i in range(1, max(1, ins.c)))
                lines.append(f"{ind}{fn}({args})")
            elif op in (Op.RET0, Op.RET1, Op.RET, Op.RETM):
                if op == Op.RET0:
                    lines.append(f"{ind}return")
                elif op == Op.RET1:
                    lines.append(f"{ind}return {regs.get(ins.a, f'slot{ins.a}')}" )
                else:
                    count = max(0, ins.d - 1)
                    vals = ", ".join(regs.get(ins.a + i, f"slot{ins.a + i}") for i in range(count))
                    lines.append(f"{ind}return {vals}".rstrip())
            elif op == Op.FNEW:
                child = proto.constants[ins.d].prototype
                if child is not None:
                    child_src = self._emit_function(child, level + 1).strip()
                    lines.append(f"{ind}local slot{ins.a} = {child_src}")
                else:
                    lines.append(f"{ind}local slot{ins.a} = function() end")
            elif op in (Op.JMP, Op.FORI, Op.FORL, Op.ITERL, Op.LOOP):
                lines.append(f"{ind}-- {op.name} target={pc + ins.d - 0x8000 + 1}")
            else:
                lines.append(f"{ind}-- {op.name} A={ins.a} B={ins.b} C={ins.c} D={ins.d}")

        if not is_root:
            lines.append("    " * level + "end")
        return "\n".join(lines) + "\n"
