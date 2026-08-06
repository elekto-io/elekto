from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("elekto")
except PackageNotFoundError:
    # Running from a source checkout that was never installed (no `pip install -e .`).
    # Not fatal: the app runs fine, only the reported version is unknown.
    __version__ = "0.0.0+unknown"
