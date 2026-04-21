from typing import Any


def to_input_json(value: Any) -> Any:
    return __import__("json").loads(__import__("json").dumps(value))
