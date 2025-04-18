__VERSION__ = None
try:
    import tomllib
    from pathlib import Path

    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    pyproject_data: dict = tomllib.load(pyproject_path.open("rb"))
    __VERSION__ = pyproject_data["project"]["version"]
except FileNotFoundError:
    pass
