"""Loads the hyphenated tool scripts as modules; tests run offline against fake API responses."""
import importlib.util
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent


def load(filename):
    spec = importlib.util.spec_from_file_location(filename.replace("-", "_").removesuffix(".py"), TOOLS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
