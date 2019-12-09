import lxml.html
import json
import time
from wtosbc import config
from wtosbc.custom_types import *
from typing import Optional, cast


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


def get_document(session: Session, url: str) -> Document:
    response = session.get(url)
    return lxml.html.document_fromstring(response.text)


# Retrieve data about product in order to POST
def get_product(doc: Document, post_item: PostItem) -> Optional[Product]:
    product: Product = {
        "id": "",
        "name": "",
        "qty": "",
        "pa": "",
        "type": "",
        "price": 0,
        "type_id": "",
        "token": "",
    }

    # TODO: divide extracting data and converting data into 2 functions
    try:
        product["id"] = doc.cssselect('input[name="products_id"]')[0].get("value")
        product["name"] = (
            doc.cssselect("title")[0]
            .text.replace(" - bike-components", "")
            .replace("buy online", "")
            .replace("online kaufen", "")
        )
        product["qty"] = str(post_item["qty"])  # TODO: store as int?
        product["pa"] = post_item["pa"]

        type_index = 0
        options = doc.cssselect("option[data-price]")

        ## TODO: move this if / else into own function for extracting price and type_id
        if post_item["type"] == "":
            option = options[type_index]
            option_type_name = get_option_type_name(option.text_content())
        else:
            option = options[type_index]
            option_type_name = get_option_type_name(option.text_content())

            # Originally we had to remove the last character, but BC changed something
            # so now we do two comparisons, with and without the last character.
            while (
                post_item["type"] != option_type_name[0:-1]
                and post_item["type"] != option_type_name
            ):
                type_index += 1
                option = options[type_index]
                option_type_name = get_option_type_name(option.text_content())

        product["type"] = post_item["type"]
        product["price"] = float(
            option.get("data-price")[0:-1].replace(",", ".")
        )  # remove last euro char
        product["type_id"] = option.get("value")

        product["token"] = doc.cssselect("body")[0].get("data-csrf-token")

        return product

    except IndexError as e:
        print("Item/type does not exist?")
        print(e)
        print(product)
        return None


def get_option_type_name(text_content: str) -> str:
    return text_content.split("|")[0].strip()


# Add a product to the cart
def add_product(session: Session, data: Product) -> None:
    response = session.post(
        "https://www.bike-components.de/callback/cart_product_add.php?ajaxCart=1",
        data={
            "products_id": data["id"],
            "id[1]": data["type_id"],
            "quantity": data["qty"],
            "ajaxCart": "1",
            "_token": data["token"],
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


# Add all orders to the cart
# and add extra data
def add_cart(
    session: Session, post_items_per_user: PostItemsPerUser
) -> OrderItemsPerUser:
    order_items_per_user: OrderItemsPerUser = {}
    # TODO: map productsPerUser to productDataPerUser and move that part out of this function
    # then call in this function add_product based on productDataPerUser

    for user, post_items in post_items_per_user.items():
        for pi, post_item in enumerate(post_items):
            if post_item is not None:
                document = get_document(session, post_item["url"])
                product = get_product(document, post_item)
                if product is not None:
                    add_product(session, product)

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
                    }
                    order_items_per_user[user].append(order)

    return order_items_per_user


def read_state() -> State:
    with open("wtosbc/state.json", "r") as file_read:
        data = json.load(file_read)
        return cast(State, data)


def remove_cart(session: Session, order_items_per_user: OrderItemsPerUser) -> None:
    state = read_state()
    for user, order_items in order_items_per_user.items():
        for pi, order_item in enumerate(order_items):
            if order_item is not None:
                # Remove price alert product from basket if state is not pa
                if (not state["pa"] and order_item["pa"] != "") or (
                    state["pa"] and order_item["pa"] == ""
                ):
                    print(
                        "Remove product ",
                        order_item["id"],
                        order_item["type_id"],
                        state["pa"],
                    )
                    remove_product(session, order_item["id"], order_item["type_id"])

    print("Removed items from cart")


def clear_cart(session: Session) -> None:
    # Get cart
    document = get_document(session, "https://www.bike-components.de/shopping_cart.php")
    token = document.cssselect("body")[0].get("data-csrf-token")

    for product in document.cssselect('input[name="products_id[]"]'):
        session.post(
            "https://www.bike-components.de/callback/cart_update.php",
            data={
                "cart_delete[]": product.get("value"),
                "products_id[]products_id": product.get("value"),
                "_token": token,
            },
        )
