"""
Reloads config in-place after resume_profile.json changes.
Call `reload_config()` any time you've just re-parsed the resume.
"""
import importlib
import config as _cfg


def reload_config() -> "config":
    return importlib.reload(_cfg)