# Python Port (luajit_decompiler_v2)

This repository now includes a Python implementation of the LuaJIT decompiler pipeline:

- LuaJIT bytecode reader/parser (header, prototypes, constants, instructions, debug info).
- Opcode model and v1/v2 opcode mapping.
- Decompiler pipeline that emits Lua-like source from parsed prototypes.
- CLI with option parity for the original binary (`-o`, `-e`, `-s`, `-f`, `-i`, `-m`, `-u`).

## Run

```bash
python -m luajit_decompiler_v2.cli INPUT_PATH [options]
```

or install editable and run:

```bash
pip install -e .
luajit-decompiler-v2-py INPUT_PATH [options]
```
