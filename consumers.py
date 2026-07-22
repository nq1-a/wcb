from collections.abc import Callable
from requests import get as wget
import wikipedia

# Types
type Config = dict[str, dict[str, str]]

type Command = list[str]
type Commands = list[Command]
type CommandExec = Callable[[Command] | [Command, Config], str]

# Registry of how many items each command consumes
consumers: dict[str, int] = {
    "echo":     -1,
    "return":    1,
    "search":   -1,
}

# Lookup table of functions associated with subcommands
consumers_lt: dict[str, dict[str, CommandExec]] = {
    "echo": {
        "_": lambda cmd:
            " ".join(cmd),
    },

    "return": {
        "status": lambda cmd:
            "online",
        "weather": lambda cmd, cfg:
            f"""
                Currently {(w := wget("https://api.weatherapi.com/v1/current.json", params={
                    "key":  cfg["tokens"]["weatherapi_com"],
                    "q":    cfg["personal"]["city"],
                }).json()["current"])["condition"]["text"].lower()}
                with a heat index of {w["heatindex_f"]}
                and humidity of {w["humidity"]} percent.
                Perceived heat index is {w["feelslike_f"]}.
            """,
    },

    "search": {
        "_": lambda cmd:
            wikipedia.summary(" ".join(cmd), sentences=2),
    },
}
