# =====================================
# generator=datazen
# version=1.7.7
# hash=f1be959be6979aa18ec8e0b543c96c3a
# =====================================

"""
vtelem - Package definition for distribution.
"""

# third-party
from vmklib.setup import setup

# internal
from vtelem import PKG_NAME, VERSION, DESCRIPTION


author_info = {
    "name": "Vaughn Kottler",
    "email": "vaughnkottler@gmail.com",
    "username": "vkottler",
}
pkg_info = {
    "name": PKG_NAME,
    "version": VERSION,
    "description": DESCRIPTION,
    "versions": [
        "3.7",
        "3.8",
        "3.9",
    ],
}
setup(
    pkg_info,
    author_info,
)
