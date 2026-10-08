"""Check the installed wheel, not the source tree: run from outside the repo."""
import importlib.resources
import re
import sys

import momo_api

assert "site-packages" in momo_api.__file__, f"imported from the source tree: {momo_api.__file__}"

with open(sys.argv[1]) as pyproject:
    version = re.search(r'^version = "([^"]+)"', pyproject.read(), re.MULTILINE).group(1)
assert momo_api.__version__ == version, f"__version__ {momo_api.__version__} != pyproject {version}"

assert importlib.resources.files("momo_api").joinpath("py.typed").is_file(), "py.typed missing"

for name in momo_api.__all__:
    getattr(momo_api, name)

print(f"ok: {len(momo_api.__all__)} exports, version {version}")
