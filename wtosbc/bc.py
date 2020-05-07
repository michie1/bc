import lxml.html
import json
import time
from wtosbc import config
from wtosbc.custom_types import *
from typing import Dict, Optional, cast, List, Tuple


def login(session: Session) -> None:
    session.get("https://www.bike-components.de/en/")
    doc = get_document(session, "https://www.bike-components.de/en/light-login/")
    token = doc.cssselect('input[name="login[_token]"]')[0].value
    print("Token retrieved: ", token)

    response = session.post(
        "https://www.bike-components.de/en/light-login/",
        data={
            "login[email]": config.email,
            "login[password]": config.password,
            "login[_token]": token,
            "login[redirect]": "",
        },
    )

    if response.text.find("Mein Konto") == -1:
        print("Not logged in")
        exit()
    print("Logged in")


# Add an order item to the cart
def add_order_item(session: Session, payload: Payload) -> None:

    response = session.post(
        "https://www.bike-components.de/en/api/v1/cart/NL/",
        data={
            "action": "add",
            "token": payload["token"],
            "option": payload["type_id"],
            "quantity": payload["quantity"],
        },
    )

    if json.loads(response.text)["action"] != "ok":
        print("Product could not be added to the cart")
        exit()


# add price alert voucher
def add_pa(session: Session, orders: OrderItemsPerUser) -> None:
    document = get_document(
        session, "https://www.bike-components.de/en/checkout/finalize/"
    )

    voucher_token = document.cssselect("#voucher__token")[0].get("value")
    print("voucher_token retrieved: ", voucher_token)

    # adding price alerts
    for user, products in orders.items():
        for pid, product in enumerate(products):
            if product is None:
                continue

            if product["pa"] != "":
                response = session.post(
                    "https://www.bike-components.de/en/checkout/finalize/",
                    data={
                        "voucher[voucher_code]": product["pa"],
                        "voucher[_token]": voucher_token,
                    },
                )
                document = lxml.html.document_fromstring(response.text)

                try:
                    pa_price = (
                        document.cssselect(
                            'div.row [data-voucher-code="' + product["pa"] + '"]'
                        )[0]
                        .getparent()
                        .getparent()
                        .getparent()
                        .cssselect(".price-single .value.discounted")[0]
                        .text.strip()
                        .replace(",", ".")[0:-1]
                    )
                    product["price"] = pa_price
                except IndexError as e:
                    print(
                        "Something wrong with price alert: " + product["pa"],
                        "maybe already used",
                    )
            time.sleep(1)


def remove_product(session: Session, product_id: str, type_id: str) -> None:
    document = get_document(session, "https://www.bike-components.de/shopping_cart.php")
    token = document.cssselect("body")[0].get("data-csrf-token")

    session.post(
        "https://www.bike-components.de/callback/cart_update.php",
        data={
            "cart_delete[]": product_id + "-" + type_id,
            "products_id[]products_id": product_id + "-" + type_id,
            "_token": token,
        },
    )


def add_order_items(session: Session, order_items_per_user: OrderItemsPerUser) -> None:
    for payload in get_payloads(order_items_per_user):
        add_order_item(session, payload)
    return None


def get_payloads(order_items_per_user: OrderItemsPerUser) -> List[Payload]:
    result: Dict[str, Payload] = {}
    for order_items in order_items_per_user.values():
        for order_item in order_items:
            key = order_item["id"] + "-" + order_item["type_id"]

            if key in result:
                result[key]["quantity"] += order_item["qty"]
            else:
                result[key] = {
                    "id": order_item["id"],
                    "type_id": order_item["type_id"],
                    "quantity": order_item["qty"],
                    "token": order_item["token"],
                }

    return list(result.values())


def get_order_items_per_user(
    session: Session, post_items_per_user: PostItemsPerUser
) -> OrderItemsPerUser:
    order_items_per_user: OrderItemsPerUser = {}

    for user, post_items in post_items_per_user.items():
        for pi, post_item in enumerate(post_items):
            if post_item is not None:
                document = get_document(session, post_item["url"])
                product = get_product(document, post_item)
                if product is not None:

                    if user not in order_items_per_user:
                        order_items_per_user[user] = []

                    order: OrderItem = {
                        "url": post_item["url"],
                        "type": post_item["type"],
                        "qty": post_item["qty"],
                        "id": product["id"],
                        "type_id": product["type_id"],
                        "price": product["price"],
                        "original_price": product["price"],
                        "price": product["price"],
                        "pa": product["pa"],
                        "name": product["name"],
                        "type": product["type"],
                        "token": product["token"],
                    }
                    order_items_per_user[user].append(order)

    return order_items_per_user


# Move to state.py
def read_state() -> State:
    with open("wtosbc/state.json", "r") as file_read:
        data = json.load(file_read)
        return cast(State, data)


def clear_cart(session: Session) -> None:
    # Get cart
    document = get_document(session, "https://www.bike-components.de/en/cart/")
    token = document.cssselect("body")[0].get("data-csrf-token")

    response = session.post(
        "https://www.bike-components.de/de/api/v1/cart/NL/",
        data={"action": "list", "token": token,},
    )
    items = response.json()["items"]
    if len(items) == 0:
        print("No items in cart")

    for item in items:
        session.post(
            "https://www.bike-components.de/de/api/v1/cart/NL/",
            data={"action": "delete", "token": token, "option": item["id"]},
        )


def get_option(post_item_type: str, doc: Document) -> Tuple[str, float, str]:
    type_index = 0
    options = doc.cssselect("option[data-price]")

    if post_item_type == "":
        option = options[type_index]
        option_type_name = get_option_type_name(option.text_content())
    else:
        option = options[type_index]
        option_type_name = get_option_type_name(option.text_content())

        # Originally we had to remove the last character, but BC changed something
        # so now we do two comparisons, with and without the last character.
        while post_item_type != remove_chars(option_type_name)[
            0:-1
        ] and post_item_type != remove_chars(option_type_name):
            type_index += 1
            option = options[type_index]
            option_type_name = get_option_type_name(option.text_content())

    price = float(
        option.get("data-price")[0:-1].replace(",", ".")
    )  # remove last euro char

    type_id: str = option.get("value")

    return (type_id, price, option_type_name)


def get_option_type_name(text_content: str) -> str:
    return text_content.split("|")[0].strip()


def get_document(session: Session, url: str) -> Document:
    response = session.get(url)
    return lxml.html.document_fromstring(response.text)


def get_product(document: Document, post_item: PostItem) -> Optional[Product]:
    try:
        (type_id, price, product_type) = get_option(
            remove_chars(post_item["type"]), document
        )

        return {
            "id": get_product_id(document),
            "name": get_product_name(document.cssselect("title")[0].text),
            "qty": post_item["qty"],
            "pa": post_item["pa"],
            "type": product_type,
            "price": price,
            "type_id": type_id,
            "token": get_product_token(document),
        }

    except IndexError as e:
        print("Item/type does not exist?")
        print(e)
        return None


def get_product_id(document: Document) -> str:
    return cast(str, document.cssselect("div.product-id>span")[0].text.strip())


def get_product_token(document: Document) -> str:
    return cast(str, document.cssselect("body")[0].get("data-csrf-token"))


def get_product_name(title: str) -> str:
    return (
        title.replace(" - bike-components", "")
        .replace("buy online", "")
        .replace("online kaufen", "")
    )


def remove_chars(value: str) -> str:
    return (
        value.replace('"', "")
        .replace("″", "")
        .replace(" ", "")
        .replace("'", "")
        .lower()
    )
