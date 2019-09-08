import os
import re
import subprocess
from typing import *

import pexpect
from PyQt5 import QtWidgets


TEMPFILE = os.path.join(os.path.dirname(__file__), "temp.rs")
TEMPFILE_CPP = os.path.join(os.path.dirname(__file__), "temp.cpp")


def disp_error(message: str):
    error = QtWidgets.QErrorMessage()
    error.showMessage(message)
    error.exec_()


def racer_enable() -> bool:
    try:
        output = subprocess.check_output(("racer", "--version"))
        if output.decode().startswith("racer"):
            return True
        else:
            return False
    except subprocess.CalledProcessError:
        return False


def debug_command(lang: str) -> str:
    if lang == "rust":
        return "env RUST_BACKTRACE=1 rust-gdb"
    if lang == "python":
        return "python -m pdb"
    else:
        return "gdb"


def compile_command(lang: str, no_debug: bool) -> List[str]:
    if lang == "rust":
        if no_debug:
            return ["rustc"]
        else:
            return ["rustc", "-g"]
    elif lang == "python":
        return ["python", "-m", "compileall"]
    else:
        if no_debug:
            return [
                "g++",
                "-std=gnu++1y",
                "-O2",
                "-I/opt/boost/gcc/include",
                "-L/opt/boost/gcc/lib",
            ]
        else:
            return [
                "g++",
                "-std=gnu++1y",
                "-g",
                "-I/opt/boost/gcc/include",
                "-L/opt/boost/gcc/lib",
            ]


def get_compiled_file(lang: str, fname: str) -> str:
    if lang == "rust":
        return "./" + os.path.basename(fname.replace(".rs", ""))
    elif lang == "python":
        return fname
    else:
        return "./a.out"


def exec_format(lang: str) -> bool:
    if lang == "rust":
        try:
            subprocess.check_output(("rustfmt", TEMPFILE), stderr=subprocess.STDOUT)
        except Exception:
            return False
    elif lang == "python":
        return True  # yet not supported
    else:
        try:
            subprocess.check_output(
                ("clang-format", "-i", TEMPFILE), stderr=subprocess.STDOUT
            )
        except Exception:
            return False
    return True


def exec_command(lang: str) -> List[str]:
    if lang == "rust":
        return ["env", "RUST_BACKTRACE=1"]
    elif lang == "python":
        return ["python"]
    else:
        return []


def indent_width(lang: str) -> int:
    if lang == "rust" or lang == "python":
        return 4
    else:
        return 2


class StateLessTextEdit(QtWidgets.QLineEdit):
    def __init__(self, value: str, parent):
        super().__init__()
        self.parent = parent
        self.setText(value)


# Need to call commit to serialize value
class StateFullTextEdit(QtWidgets.QLineEdit):
    def __init__(self, settings, name: str, parent, default: Optional[str] = None):
        super().__init__()
        self.parent = parent
        self.settings = settings
        self.name = name
        v = settings.value(name, type=str)
        self.setText(v)
        if not v and default is not None:
            self.setText(default)

    def commit(self):
        self.settings.setValue(self.name, self.text())


class StateFullCheckBox(QtWidgets.QCheckBox):
    def __init__(self, settings, name: str, parent):
        super().__init__()
        self.parent = parent
        self.settings = settings
        self.name = name
        v = settings.value(name, type=bool)
        self.setChecked(v)

    def commit(self):
        self.settings.setValue(self.name, self.isChecked())


def get_resources_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "resources")


def wait_input_ready(debug_process: pexpect.spawn, lang: str, timeout: Optional[float] = None):
    if lang == "python":
        debug_process.expect("\(Pdb\)", timeout=timeout)
    else:
        debug_process.expect("\(gdb\)", timeout=timeout)

def get_executing_line(lang: str, line: str) -> Optional[int]:
    if lang == "python":
        if line.endswith("<module>()"):
            match = re.search(r"(\()(.*?)\)", line)
            return int(match.groups()[-1])
    else:
        try:
            line_num = int(line.split("\t")[0])
            return line_num
        except ValueError:
            return None
    return None
