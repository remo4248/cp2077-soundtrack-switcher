"""The patch must bring everything it references. It once did not: it added #include "StopOn.hpp"
without the file, so `git apply --check` passed and the result would not have compiled.

Usage: python tools/check_patch.py <folder holding the patched AudioXL checkout>
"""
import os, re, sys

root = os.path.join(sys.argv[1], 'plugin', 'src')
missing = []
for f in os.listdir(root):
    if not f.endswith(('.cpp', '.hpp')):
        continue
    for inc in re.findall(r'#include\s+"([^"]+)"', open(os.path.join(root, f), encoding='utf-8').read()):
        if not os.path.exists(os.path.join(root, inc)):
            missing.append(f'{f} includes {inc}, which is not in the tree')
if missing:
    sys.exit('patch is incomplete:\n  ' + '\n  '.join(missing))
print(f'ok - every local include in {root} resolves')
