import requests
import lxml.html
import xmltodict
from urllib.request import urlopen
import json
import ssl
from typing import cast, Tuple

from wtosbc import config, spreadsheet
from wtosbc.custom_types import *

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def increment_bc_number(number: int) -> None:
    print("increment bc number")
    with open("wtosbc/state.json", "r") as file_read:
        data = json.load(file_read)
        with open("wtosbc/state.json", "w") as file_write:
            data["number"] = number
            json.dump(data, file_write)


def create_next_sheet(number: int) -> None:
    print("create next sheet")
    spreadsheet.create_sheet(number)


def set_state_pa() -> None:
    print("set PA state")
    with open("wtosbc/state.json", "r") as file_read:
        data = json.load(file_read)
        with open("wtosbc/state.json", "w") as file_write:
            data["state"] = True
            json.dump(data, file_write)


def reset_state_pa() -> None:
    print("reset PA state")
    with open("wtosbc/state.json", "r") as file_read:
        data = json.load(file_read)
        with open("wtosbc/state.json", "w") as file_write:
            data["state"] = False
            json.dump(data, file_write)


def load_posts(bc_number: int) -> Posts:
    token = config.wtos_token

    with urlopen(
        "https://wtos.nl/bc.php?token=" + token + "&number=" + str(bc_number)
    ) as url:
        return cast(Posts, json.loads(url.read().decode()))


def get_post_items_per_user(bc_number: int, posts: Posts) -> PostItemsPerUser:
    bc_chef = config.bc_chef
    post_items_per_user: PostItemsPerUser = {}

    for post in posts:
        content = post["post_content"]
        user = post["display_name"]

        if content[2:11] == str(int(bc_number) + 1) + " start":  # next start
            # TODO: Check if you can do this outside/before this function
            if user == bc_chef:
                increment_bc_number(bc_number + 1)
                reset_state_pa()
                create_next_sheet(bc_number + 1)
                break
        elif content[2:11] == str(bc_number + 1) + " PA":  # next start
            # TODO: Check if you can do this outside/before this function
            if user == bc_chef:
                set_state_pa()
                break
        elif content[2:11] == str(bc_number) + " start":  # current start
            print("start")
        elif content[2:5] == str(bc_number):  # BC123
            extract_post_items(content, user, post_items_per_user)

    return post_items_per_user


def extract_post_items(
    content: str, user: str, post_items_per_user: PostItemsPerUser
) -> None:
    bc_chef = config.bc_chef
    if user not in post_items_per_user:
        post_items_per_user[user] = []
    lines = content.split("\n")[1:]
    for line in lines:
        line = (
            line.replace("\u00a0", " ")
            .replace("<strong>", "[b]")
            .replace("</strong>", "[/b]")
        )

        if line == "" or line == "&nbsp;" or (line[0] == "-" and line[-1] == "-"):
            continue

        if line == "---" or line == "--" or line == "—":
            break

        if line == "WTOS":
            if user == bc_chef:
                user = "WTOS"
                post_items_per_user[user] = []
            break

        try:
            product_qty_str, product = line.split("x ", 1)
            product_qty = int(product_qty_str.strip())
        except ValueError as e:
            print("ValueError")
            print(e)
            print(line)
            continue

        if product_qty > 0:
            (product_url, type_pa) = split_url_type_pa(product)

            if "bike-components.de" in product_url:
                (product_type, product_pa) = split_type_pa(type_pa)

                # fix for " in type
                product_type = (
                    product_type.replace("&quot;", '"').replace("&nbsp;", "").strip()
                )

                post_items_per_user[user].append(
                    {
                        "url": product_url,
                        "type": product_type,
                        "qty": product_qty,
                        "pa": product_pa,
                    }
                )
            else:
                print("Wrong url: ", product_url)


def split_url_type_pa(product: str) -> Tuple[str, str]:
    splitted = product.split(" ")
    product_url = splitted[0]
    type_pa = " ".join(splitted[1:])
    return (product_url, type_pa)


def split_type_pa(type_pa: str) -> Tuple[str, str]:
    strong = type_pa.split("[b]")

    if len(strong) == 2:
        # type and PA exists
        product_type = strong[0].strip()
        product_pa = strong[1].replace("[/b]", "").strip()
    else:
        # type or PA
        if type_pa[0:8] == "<strong>":
            product_pa = type_pa[8:-9]
            product_type = ""
        else:
            product_type = type_pa
            product_pa = ""

    return (product_type, product_pa)
