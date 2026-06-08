import dataclasses as dc
from typing import Any


@dc.dataclass(slots=True)
class Item(object):
    def get(self, key: str) -> Any:
        """ get attribute value """
        return getattr(self, key)

    def as_dict(self) -> dict:
        return dc.asdict(self)

    def __iter__(self):
        for f in dc.fields(self):
            yield f.name, getattr(self, f.name)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any):
        setattr(self, key, value)

    def __str__(self) -> str:
        return str(dc.asdict(self))

    def __hash__(self):
        return hash(
            tuple(self)
        )
