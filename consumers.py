from collections.abc import Callable

consumers: dict[str, int] = {
    "return": 1,
}

consumers_lt: dict[str, dict[str, Callable[[list[str]], str]]] = {
    "return": {
        "status": lambda cmd: "online",
    },
}
