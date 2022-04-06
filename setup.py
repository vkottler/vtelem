# =====================================
# generator=datazen
# version=2.1.0
# hash=4e49ea9730f8b8f8ccaeb609d4150a75
# =====================================

"""
vtelem - Package definition for distribution.
"""

# third-party
try:
    from vmklib.setup import setup
except (ImportError, ModuleNotFoundError):
    from vtelem_bootstrap.setup import setup  # type: ignore

# internal
from vtelem import DESCRIPTION, PKG_NAME, VERSION

author_info = {
    "name": "Vaughn Kottler",
    "email": "vaughnkottler@gmail.com",
    "username": "vkottler",
}
pkg_info = {
    "name": PKG_NAME,
    "slug": PKG_NAME.replace("-", "_"),
    "version": VERSION,
    "description": DESCRIPTION,
    "versions": [
        "3.7",
        "3.8",
        "3.9",
        "3.10",
    ],
}
setup(
    pkg_info,
    author_info,
)
