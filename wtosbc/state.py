import json
from typing import cast
from wtosbc.custom_types import *


def load_bc_number() -> int:
    with open("wtosbc/state.json", "r") as fp:
        data = json.load(fp)
        return int(data["number"])


def set_bc_number(number: int) -> None:
    with open("wtosbc/state.json", "r") as file_read:
        data = json.load(file_read)
        with open("wtosbc/state.json", "w") as file_write:
            data["number"] = number
            json.dump(data, file_write)


def read_pa_state() -> State:
    with open("wtosbc/state.json", "r") as file_read:
        data = json.load(file_read)
        return cast(State, data)
