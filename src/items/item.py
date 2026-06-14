import datetime as dt

import dataclasses as dc
from typing import Any, Optional


@dc.dataclass(slots=True)
class Item(object):
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """ get attribute value """
        return getattr(self, key, default)

    def as_dict(self) -> dict[str, Any]:
        def serializable(value: Any) -> Any:
            """ serialize value to jsonable format """
            if isinstance(value, (dt.datetime, dt.date)):
                return value.isoformat()

            if dc.is_dataclass(value):
                return serializable(dc.asdict(value))

            if isinstance(value, dict):
                return {k: serializable(v) for k, v in value.items()}

            if isinstance(value, (list, tuple, set)):
                return [serializable(v) for v in value]

            return value

        return serializable(dc.asdict(self))

    def __iter__(self):
        for f in dc.fields(self):
            yield f.name, getattr(self, f.name)

    def __getitem__(self, key: str, default: Optional[Any] = None) -> Any:
        return getattr(self, key, default)

    def __setitem__(self, key: str, value: Any):
        setattr(self, key, value)

    def __str__(self) -> str:
        return str(dc.asdict(self))

    def __hash__(self):
        return hash(
            tuple(self)
        )
