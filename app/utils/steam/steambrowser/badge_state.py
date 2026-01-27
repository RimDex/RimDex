from enum import Enum


class BadgeState(str, Enum):
    INSTALLED = "installed"
    ADDED = "added"
    DEFAULT = "default"
