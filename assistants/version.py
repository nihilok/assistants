import importlib.metadata

__VERSION__ = None
try:
    # First try to get version from package metadata (works when installed)
    __VERSION__ = importlib.metadata.version("assistants-framework")
except importlib.metadata.PackageNotFoundError:
    # Fallback to reading pyproject.toml (for development)
    try:
        import tomllib
        from pathlib import Path

        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        pyproject_data = tomllib.load(pyproject_path.open("rb"))
        __VERSION__ = pyproject_data["project"]["version"]
    except (FileNotFoundError, KeyError):
        pass
