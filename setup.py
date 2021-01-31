# =====================================
# generator=datazen
# version=1.3.1
# hash=d05f95c0b6ef348bbfba8e35f883a74d
# =====================================

"""
vtelem - Package definition for distribution.
"""

# third-party
from vmklib.setup import setup  # type: ignore

# internal
from vtelem import PKG_NAME, VERSION, DESCRIPTION


author_info = {"name": "Vaughn Kottler",
               "email": "vaughnkottler@gmail.com",
               "username": "vkottler"}
pkg_info = {"name": PKG_NAME, "version": VERSION, "description": DESCRIPTION}
setup(
    pkg_info,
    author_info,
)
