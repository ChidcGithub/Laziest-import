"""
Final comprehensive test: identify exact root cause.
"""
# ruff: noqa: S603 — all subprocess calls use list form, not shell=True

import os
import subprocess
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(base_dir)


def check_search():
    r = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, '.'); from laziest_import import lz; r1=lz.symbol.search('numpy'); r2=lz.symbol.search('pytest'); print('numpy=%d,pytest=%d'%(len(r1),len(r2)))",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=base_dir,
        check=True,
    )
    for line in r.stdout.strip().splitlines():
        if line.startswith("numpy="):
            parts = line.split(",")
            return int(parts[0].split("=")[1]) > 0 or int(parts[1].split("=")[1]) > 0
    return False


# Build fresh cache
subprocess.run(
    [
        sys.executable,
        "-c",
        "import sys; sys.path.insert(0, '.'); from laziest_import._symbol import rebuild_symbol_index; rebuild_symbol_index()",
    ],
    capture_output=True,
    timeout=120,
    cwd=base_dir,
    check=True,
)
print("Fresh cache:", "WORKS" if check_search() else "FAILS")

# Run section 13 only (symbol.index.rebuild)
print("\n=== Testing section 13 only ===")
script = r"""
import sys, os
_f = os.path.join(os.getcwd(), 'tests', 'test_comprehensive_usage.py')
sys.path.insert(0, os.path.dirname(os.path.dirname(_f)))
# Read comprehensive test and extract only section 13
with open(_f, 'r') as f:
    content = f.read()
import re
section_pattern = re.compile(r'^\s*section\(\s*"\d+\.', re.MULTILINE)
matches = list(section_pattern.finditer(content))
# Find section 13
sec13_start = None
sec13_end = None
for i, m in enumerate(matches):
    line = content[m.start():m.start()+50]
    if '"13.' in line:
        sec13_start = m.start()
        sec13_end = matches[i+1].start() if i+1 < len(matches) else len(content)
        break
# Run preamble + section 13
preamble = content[:matches[0].start()]
code = preamble + content[sec13_start:sec13_end]
exec(compile(code, _f, 'exec'), {'__file__': _f, '__name__': '__main__'})
"""
subprocess.run(
    [sys.executable, "-c", script], capture_output=True, timeout=120, cwd=base_dir, check=True
)
w13 = check_search()
print("After section 13 only:", "WORKS" if w13 else "FAILS")

# Run section 33 (reset_all) only
print("\n=== Testing section 33 only ===")
subprocess.run(
    [
        sys.executable,
        "-c",
        "import sys; sys.path.insert(0, '.'); from laziest_import._symbol import rebuild_symbol_index; rebuild_symbol_index()",
    ],
    capture_output=True,
    timeout=120,
    cwd=base_dir,
    check=True,
)
script2 = r"""
import sys, os
_f = os.path.join(os.getcwd(), 'tests', 'test_comprehensive_usage.py')
sys.path.insert(0, os.path.dirname(os.path.dirname(_f)))
with open(_f, 'r') as f:
    content = f.read()
import re
section_pat = re.compile(r'^\s*section\(\s*"\d+\.', re.MULTILINE)
matches = list(section_pat.finditer(content))
# Find section 33
sec33_start = None
sec33_end = None
for i, m in enumerate(matches):
    line = content[m.start():m.start()+50]
    if '"33.' in line:
        sec33_start = m.start()
        sec33_end = matches[i+1].start() if i+1 < len(matches) else len(content)
        break
preamble = content[:matches[0].start()]
# Include section 7 (compression) too since it's needed before 33
sec7_start = None
sec7_end = None
for i, m in enumerate(matches):
    if '"7.' in content[m.start():m.start()+50]:
        sec7_start = m.start()
        sec7_end = matches[i+1].start() if i+1 < len(matches) else None
        break
code = preamble + content[sec7_start:sec7_end] + content[sec33_start:sec33_end]
exec(compile(code, _f, 'exec'), {'__file__': _f, '__name__': '__main__'})
"""
subprocess.run(
    [sys.executable, "-c", script2], capture_output=True, timeout=120, cwd=base_dir, check=True
)
w33 = check_search()
print("After section 33 only (with 7):", "WORKS" if w33 else "FAILS")

# Test with ALL sections
print("\n=== Testing ALL sections ===")
subprocess.run(
    [
        sys.executable,
        "-c",
        "import sys; sys.path.insert(0, '.'); from laziest_import._symbol import rebuild_symbol_index; rebuild_symbol_index()",
    ],
    capture_output=True,
    timeout=120,
    cwd=base_dir,
    check=True,
)
script3 = r"""
import sys, os
_f = os.path.join(os.getcwd(), 'tests', 'test_comprehensive_usage.py')
sys.path.insert(0, os.path.dirname(os.path.dirname(_f)))
exec(compile(open(_f).read(), _f, 'exec'), {'__file__': _f, '__name__': '__main__'})
"""
subprocess.run(
    [sys.executable, "-c", script3], capture_output=True, timeout=180, cwd=base_dir, check=True
)
wall = check_search()
print("After ALL sections:", "WORKS" if wall else "FAILS")

# Key test: run ALL sections WITHOUT sections 13 and 33
print("\n=== Testing ALL sections except 13 and 33 ===")
subprocess.run(
    [
        sys.executable,
        "-c",
        "import sys; sys.path.insert(0, '.'); from laziest_import._symbol import rebuild_symbol_index; rebuild_symbol_index()",
    ],
    capture_output=True,
    timeout=120,
    cwd=base_dir,
    check=True,
)
script4 = r"""
import sys, os
_f = os.path.join(os.getcwd(), 'tests', 'test_comprehensive_usage.py')
sys.path.insert(0, os.path.dirname(os.path.dirname(_f)))
with open(_f, 'r') as f:
    content = f.read()
import re
section_pat = re.compile(r'^\s*section\(\s*"\d+\.', re.MULTILINE)
matches = list(section_pat.finditer(content))

# Build code without sections 13 and 33
code = content[:matches[0].start()]  # preamble
skip_sections = {13, 33}
for i, m in enumerate(matches):
    num = int(content[m.start()+9:m.start()+11].strip('". '))
    if num in skip_sections:
        continue
    end = matches[i+1].start() if i+1 < len(matches) else len(content)
    code += content[m.start():end]

exec(compile(code, _f, 'exec'), {'__file__': _f, '__name__': '__main__'})
"""
subprocess.run(
    [sys.executable, "-c", script4], capture_output=True, timeout=180, cwd=base_dir, check=True
)
wex = check_search()
print("Without sections 13 and 33:", "WORKS" if wex else "FAILS")

# Test: without section 13 only
print("\n=== Testing ALL sections except 13 ===")
subprocess.run(
    [
        sys.executable,
        "-c",
        "import sys; sys.path.insert(0, '.'); from laziest_import._symbol import rebuild_symbol_index; rebuild_symbol_index()",
    ],
    capture_output=True,
    timeout=120,
    cwd=base_dir,
    check=True,
)
script5 = r"""
import sys, os
_f = os.path.join(os.getcwd(), 'tests', 'test_comprehensive_usage.py')
sys.path.insert(0, os.path.dirname(os.path.dirname(_f)))
with open(_f, 'r') as f:
    content = f.read()
import re
section_pat = re.compile(r'^\s*section\(\s*"\d+\.', re.MULTILINE)
matches = list(section_pat.finditer(content))
code = content[:matches[0].start()]
for i, m in enumerate(matches):
    num = int(content[m.start()+9:m.start()+11].strip('". '))
    if num == 13:
        continue
    end = matches[i+1].start() if i+1 < len(matches) else len(content)
    code += content[m.start():end]
exec(compile(code, _f, 'exec'), {'__file__': _f, '__name__': '__main__'})
"""
subprocess.run(
    [sys.executable, "-c", script5], capture_output=True, timeout=180, cwd=base_dir, check=True
)
wno13 = check_search()
print("Without section 13:", "WORKS" if wno13 else "FAILS")
