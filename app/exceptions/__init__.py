from ..schemas.utils import PyObjectId


class DocumentNotFound(Exception):
    def __init__(self, id: PyObjectId):
        self.id = id


__all__ = [
    "DocumentNotFound"
]
