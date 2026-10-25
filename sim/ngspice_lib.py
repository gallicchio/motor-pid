"""Minimal ctypes wrapper around libngspice (shared library), no PySpice."""
import ctypes, ctypes.util, os, sys

class _Vec(ctypes.Structure):
    _fields_ = [("name", ctypes.c_char_p), ("type", ctypes.c_int), ("flags", ctypes.c_short),
                ("creal", ctypes.POINTER(ctypes.c_double)), ("ccomplex", ctypes.c_void_p),
                ("length", ctypes.c_int)]
class _Cplx(ctypes.Structure):
    _fields_ = [("re", ctypes.c_double), ("im", ctypes.c_double)]

SEND = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
STAT = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
EXIT = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_bool, ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)
DATA = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)
INIT = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p)
BGRUN = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)

class NgSpice:
    def __init__(self, lib=None, quiet=True):
        lib = lib or os.environ.get("LIBNGSPICE") or ctypes.util.find_library("ngspice") or "libngspice.so.0"
        self.lib = ctypes.CDLL(lib)
        self.log = []
        self._send = SEND(self._on_send); self._stat = STAT(lambda s, i, p: 0)
        self._exit = EXIT(lambda s, b, c, i, p: 0); self._data = DATA(lambda a, b, c, d: 0)
        self._init = INIT(lambda a, b, c: 0); self._bg = BGRUN(lambda a, b, c: 0)
        self.quiet = quiet
        self.lib.ngSpice_Init(self._send, self._stat, self._exit, self._data, self._init, self._bg, None)
        self.lib.ngSpice_Command.argtypes = [ctypes.c_char_p]
        self.lib.ngGet_Vec_Info.restype = ctypes.POINTER(_Vec)
        self.lib.ngGet_Vec_Info.argtypes = [ctypes.c_char_p]
        self.lib.ngSpice_Circ.argtypes = [ctypes.POINTER(ctypes.c_char_p)]
    def _on_send(self, s, i, p):
        self.log.append(s.decode(errors="replace"))
        if not self.quiet: print(s.decode(errors="replace"))
        return 0
    def cmd(self, c):
        return self.lib.ngSpice_Command(c.encode())
    def circuit(self, lines):
        arr = (ctypes.c_char_p * (len(lines) + 1))()
        for i, l in enumerate(lines): arr[i] = l.encode()
        arr[len(lines)] = None
        return self.lib.ngSpice_Circ(arr)
    def vec(self, name):
        v = self.lib.ngGet_Vec_Info(name.encode())
        if not v: raise KeyError(name)
        v = v.contents
        n = v.length
        if v.flags & 2 and v.ccomplex:  # VF_COMPLEX = 2
            arr = ctypes.cast(v.ccomplex, ctypes.POINTER(_Cplx))
            return [complex(arr[i].re, arr[i].im) for i in range(n)]
        return [v.creal[i] for i in range(n)]

if __name__ == "__main__":
    ng = NgSpice(quiet=True)
    ng.circuit(["test", "V1 1 0 dc 1 ac 1", "R1 1 2 1k", "C1 2 0 1u", ".end"])
    ng.cmd("op")
    print("op v(2) =", ng.vec("v(2)"))
    ng.cmd("ac dec 2 10 10k")
    print("ac v(2) =", [abs(x) for x in ng.vec("v(2)")][:6])
    print("ngspice says:", [l for l in ng.log if "ngspice" in l.lower()][:2])
