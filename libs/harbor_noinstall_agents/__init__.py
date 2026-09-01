"""Harbor agent adapters, imported lazily so helper modules stay standalone."""

from importlib import import_module

__all__ = [
    "NoInstallHaitun",
    "NoInstallHaitunMethod",
    "NoInstallClaudeCode",
    "NoInstallCodex",
    "NoInstallQwenCode",
    "NoInstallKimiCli",
]


def __getattr__(name: str):
    if name not in __all__:
        raise AttributeError(name)
    return getattr(import_module(".agents", __name__), name)
