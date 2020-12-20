# =====================================
# generator=datazen
# version=1.2.1
# hash=c8e415b0f05c18b314a04f4bb5ece561
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
