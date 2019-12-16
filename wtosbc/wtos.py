import requests
import lxml.html
import xmltodict
from urllib.request import urlopen
import json
import ssl
from typing import cast, Tuple

from wtosbc import config, spreadsheet, state
from wtosbc.custom_types import *

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def create_sheet(number: int) -> None:
    print("create sheet")
    spreadsheet.create_sheet(number)


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

        if content[2:11] == str(bc_number) + " start":  # current start
            print("start")
        elif content[2:5] == str(bc_number):  # BC123
            extract_post_items(content, user, post_items_per_user)
        elif is_next_start_post(post, bc_number, bc_chef):
            break
        elif content[2:11] == str(bc_number + 1) + " PA":  # next start
            # TODO: Check if you can do this outside this function
            if user == bc_chef:
                state.enable_pa_state()
                break

    return post_items_per_user


def has_next_post(posts: Posts, bc_number: int, bc_chef: str) -> bool:
    return any(is_next_start_post(post, bc_number, bc_chef) for post in posts)


def is_next_start_post(post: Post, bc_number: int, bc_chef: str) -> bool:
    content = post["post_content"]
    user = post["display_name"]

    return content[2:11] == str(bc_number + 1) + " start" and user == bc_chef


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
    bold = type_pa.strip().split("[b]")

    if len(bold) == 1:
        # only type exists
        product_type = type_pa.strip()
        product_pa = ""
    else:
        if bold[0].strip() == "":  # only PA exists
            product_type = ""
            product_pa = bold[1].replace("[/b]", "").strip()
        else:  # type and PA exists
            product_type = bold[0].strip()
            product_pa = bold[1].replace("[/b]", "").strip()

    return (product_type, product_pa)
