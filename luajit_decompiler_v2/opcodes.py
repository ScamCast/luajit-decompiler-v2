from __future__ import annotations

from enum import IntEnum

BC_OP_JMP_BIAS = 0x8000


class Op(IntEnum):
    ISLT = 0
    ISGE = 1
    ISLE = 2
    ISGT = 3
    ISEQV = 4
    ISNEV = 5
    ISEQS = 6
    ISNES = 7
    ISEQN = 8
    ISNEN = 9
    ISEQP = 10
    ISNEP = 11
    ISTC = 12
    ISFC = 13
    IST = 14
    ISF = 15
    ISTYPE = 16
    ISNUM = 17
    MOV = 18
    NOT = 19
    UNM = 20
    LEN = 21
    ADDVN = 22
    SUBVN = 23
    MULVN = 24
    DIVVN = 25
    MODVN = 26
    ADDNV = 27
    SUBNV = 28
    MULNV = 29
    DIVNV = 30
    MODNV = 31
    ADDVV = 32
    SUBVV = 33
    MULVV = 34
    DIVVV = 35
    MODVV = 36
    POW = 37
    CAT = 38
    KSTR = 39
    KCDATA = 40
    KSHORT = 41
    KNUM = 42
    KPRI = 43
    KNIL = 44
    UGET = 45
    USETV = 46
    USETS = 47
    USETN = 48
    USETP = 49
    UCLO = 50
    FNEW = 51
    TNEW = 52
    TDUP = 53
    GGET = 54
    GSET = 55
    TGETV = 56
    TGETS = 57
    TGETB = 58
    TGETR = 59
    TSETV = 60
    TSETS = 61
    TSETB = 62
    TSETM = 63
    TSETR = 64
    CALLM = 65
    CALL = 66
    CALLMT = 67
    CALLT = 68
    ITERC = 69
    ITERN = 70
    VARG = 71
    ISNEXT = 72
    RETM = 73
    RET = 74
    RET0 = 75
    RET1 = 76
    FORI = 77
    JFORI = 78
    FORL = 79
    IFORL = 80
    JFORL = 81
    ITERL = 82
    IITERL = 83
    JITERL = 84
    LOOP = 85
    ILOOP = 86
    JLOOP = 87
    JMP = 88
    FUNCF = 89
    IFUNCF = 90
    JFUNCF = 91
    FUNCV = 92
    IFUNCV = 93
    JFUNCV = 94
    FUNCC = 95
    FUNCCW = 96


UNSUPPORTED = {
    Op.ISTYPE,
    Op.ISNUM,
    Op.TGETR,
    Op.TSETR,
    Op.JFORI,
    Op.IFORL,
    Op.JFORL,
    Op.IITERL,
    Op.JITERL,
    Op.ILOOP,
    Op.JLOOP,
    Op.FUNCF,
    Op.IFUNCF,
    Op.JFUNCF,
    Op.FUNCV,
    Op.IFUNCV,
    Op.JFUNCV,
    Op.FUNCC,
    Op.FUNCCW,
}

ABC_FORMAT = {
    Op.ADDVN, Op.SUBVN, Op.MULVN, Op.DIVVN, Op.MODVN,
    Op.ADDNV, Op.SUBNV, Op.MULNV, Op.DIVNV, Op.MODNV,
    Op.ADDVV, Op.SUBVV, Op.MULVV, Op.DIVVV, Op.MODVV,
    Op.POW, Op.CAT, Op.TGETV, Op.TGETS, Op.TGETB, Op.TGETR,
    Op.TSETV, Op.TSETS, Op.TSETB, Op.TSETR,
    Op.CALLM, Op.CALL, Op.ITERC, Op.ITERN, Op.VARG,
}


def map_opcode(byte: int, version: int) -> Op:
    if version == 1 and byte >= Op.ISTYPE:
        if byte >= Op.TGETR - 2:
            if byte >= Op.TSETR - 3:
                byte += 4
            else:
                byte += 3
        else:
            byte += 2
    return Op(byte)
