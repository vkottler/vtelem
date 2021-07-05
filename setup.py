# =====================================
# generator=datazen
# version=1.7.4
# hash=e4ae7136bfdedaebc4be3f24ec1519b6
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
pkg_info = {"name": PKG_NAME, "version": VERSION, "description": DESCRIPTION}
setup(
    pkg_info,
    author_info,
)
