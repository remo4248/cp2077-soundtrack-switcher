"""Every header our patch starts including must be a file the patch also brings.

It once wasn't: the patch added #include "StopOn.hpp" without StopOn.hpp or StopOn.cpp, so
`git apply --check` passed and the result could not compile. Upstream's own includes are left
alone - they resolve through include paths this check knows nothing about.

Usage: python tools/check_patch.py <patch file> <folder holding the patched checkout>
"""
import os, re, sys

patch, tree = sys.argv[1], sys.argv[2]
added = re.findall(r'^\+\s*#include\s+"([^"]+)"', open(patch, encoding='utf-8').read(), re.M)
present = {f for _, _, files in os.walk(tree) for f in files}
missing = sorted({inc for inc in added if os.path.basename(inc) not in present})
if missing:
    sys.exit('patch adds includes for files it does not bring:\n  ' + '\n  '.join(missing))
print(f'ok - the {len(set(added))} include(s) the patch adds are all in the tree')
