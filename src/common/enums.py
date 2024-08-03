from enum import Enum


class Action(str, Enum):
    DOWNLOAD = "download"
    PROCESS = "process"
    DELETE = "delete"
