# =====================================
# generator=datazen
# version=1.7.7
# hash=0edc258f2b3c30dc681f1b952a4494cc
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
    ],
}
setup(
    pkg_info,
    author_info,
)
