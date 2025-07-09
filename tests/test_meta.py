import tomllib
from pathlib import Path

import sector


def test_release_version() -> None:
    pyproject_file = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_file, "rb") as pf:
        data = tomllib.load(pf)
        version = data["project"]["version"]

    assert (
        sector.__version__ == version
    ), "Version of the library is not the same as the project version"
