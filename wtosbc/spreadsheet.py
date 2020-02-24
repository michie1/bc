import json
import gspread
import math
from oauth2client.service_account import ServiceAccountCredentials
import time
from typing import Any, cast
from wtosbc import config
from wtosbc.custom_types import *


def load(bc_number: int) -> Spreadsheet:
    print("Load Google credentials")
    scope = ["https://spreadsheets.google.com/feeds"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "wtosbc/credentials.json", scope
    )

    client = gspread.authorize(credentials)
    bc_spreadsheet = client.open_by_key(config.spreadsheet_key)
    bc_spreadsheet.worksheets()  # problem if this is removed

    return bc_spreadsheet


def update(
    bc_spreadsheet: Spreadsheet, bc_number: int, order_items_per_user: OrderItemsPerUser
) -> None:
    reset(bc_spreadsheet, bc_number)
    worksheet = add_worksheet(bc_spreadsheet, bc_number)
    cells = get_cells(order_items_per_user)
    update_cells(worksheet, cells)


def create_sheet(bc_number: int) -> None:
    print("Load Google credentials")
    scope = ["https://spreadsheets.google.com/feeds"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "wtosbc/credentials.json", scope
    )

    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(config.spreadsheet_key)

    sh.worksheets()  # problem if this is removed
    sh.add_worksheet(title="BC" + str(bc_number), rows="1", cols="1")


def reset(bc_spreadsheet: Spreadsheet, bc_number: int) -> None:
    bc_spreadsheet.add_worksheet(title="0", rows="1", cols="1")

    try:
        # delete worksheet
        bc_spreadsheet.del_worksheet(bc_spreadsheet.worksheet("BC" + str(bc_number)))
    except gspread.exceptions.WorksheetNotFound as err:
        print(err)

    bc_spreadsheet.del_worksheet(bc_spreadsheet.worksheet("0"))


def add_worksheet(bc_spreadsheet: Spreadsheet, bc_number: int) -> Worksheet:
    return bc_spreadsheet.add_worksheet(
        title="BC" + str(bc_number), rows="200", cols="10"
    )


def get_cells(orders: OrderItemsPerUser) -> Cells:
    cells: Cells = [""] * 2000
    row_number = 0

    cells[4] = "Price alert"
    cells[5] = "Originele prijs"
    cells[6] = "Prijs per stuk"
    cells[7] = "Aantal"
    cells[8] = "Totaal"
    cells[9] = "5%"
    row_number += 1

    summary = []

    for user, products in sorted(orders.items()):
        if len(products) > 0:
            cells[row_number * 10] = user
            row_number += 1
            first_row = row_number

            for product in products:
                if product is None:
                    continue

                try:
                    (cells[row_number * 10 + 0], cells[row_number * 10 + 1]) = product[
                        "name"
                    ].split(" ", 1)
                except IndexError as e:
                    print("index error", e)
                    print(user, product)
                    print(product["type"])
                    print(row_number)
                    continue
                except KeyError as e:
                    print("key error", e)
                    print(user, product)
                    continue

                cells[row_number * 10 + 2] = product["type"]
                cells[row_number * 10 + 4] = product["pa"]

                cells[row_number * 10 + 5] = str(product["original_price"])
                cells[row_number * 10 + 6] = str(product["price"])

                cells[row_number * 10 + 7] = str(product["qty"])
                cells[row_number * 10 + 8] = (
                    "=G" + str(row_number + 1) + "*H" + str(row_number + 1)
                )
                cells[row_number * 10 + 9] = (
                    "=CEILING(0.95*I" + str(row_number + 1) + ",0.01)"
                )
                row_number += 1

            last_row = row_number - 1

            cells[row_number * 10 + 8] = (
                "=SUM(I" + str(first_row + 1) + ":I" + str(last_row + 1) + ")"
            )
            cells[row_number * 10 + 9] = (
                "=SUM(J" + str(first_row + 1) + ":J" + str(last_row + 1) + ")"
            )

            summary.append(
                (user, "=SUM(J" + str(first_row + 1) + ":J" + str(last_row + 1) + ")")
            )

            row_number += 2

    start_row_total_sum = row_number + 1
    for user_sum in summary:
        cells[row_number * 10] = user_sum[0]
        cells[row_number * 10 + 1] = user_sum[1]
        row_number += 1
    end_row_total_sum = row_number

    row_number += 1

    cells[row_number * 10] = "Totaal"
    cells[row_number * 10 + 1] = (
        "=SUM(B" + str(start_row_total_sum) + ":B" + str(end_row_total_sum) + ")"
    )
    row_number += 1

    cells[row_number * 10] = "zonder 5%"
    cells[row_number * 10 + 1] = "=B" + str((row_number)) + "/0.95"
    row_number += 1

    cells[row_number * 10] = "Met porto"
    cells[row_number * 10 + 1] = "=B" + str((row_number)) + "+5.95"
    row_number += 1

    return cells


def update_cells(worksheet: Worksheet, cells: Cells) -> None:
    worksheet_cells = worksheet.range("A1:J%s" % 200)
    for index, cell in enumerate(cells):
        worksheet_cells[index].value = cell
    worksheet.update_cells(worksheet_cells, value_input_option="USER_ENTERED")
