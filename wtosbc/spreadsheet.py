import json
import gspread
import math
from oauth2client.service_account import ServiceAccountCredentials
import time
from typing import Any
from wtosbc import config
from wtosbc.custom_types import *


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


def update_worksheet(worksheet: Worksheet, orders: OrderItemsPerUser) -> None:
    # TODO: retrieve cells from parameter

    cell_list = worksheet.range("A1:J%s" % 200)

    row_number = 0

    cell_list[4].value = "Price alert"
    cell_list[5].value = "Originele prijs"
    cell_list[6].value = "Prijs per stuk"
    cell_list[7].value = "Aantal"
    cell_list[8].value = "Totaal"
    cell_list[9].value = "5% (mits geen PA)"
    row_number += 1

    summary = []

    for user, products in sorted(orders.items()):
        if len(products) > 0:
            cell_list[row_number * 10].value = user  # no decode ni python 3.5
            row_number += 1
            first_row = row_number

            for product in products:
                if product is None:
                    continue

                try:
                    (
                        cell_list[row_number * 10 + 0].value,
                        cell_list[row_number * 10 + 1].value,
                    ) = (product["name"].decode("utf-8").split(" ", 1))
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

                cell_list[row_number * 10 + 2].value = product["type"]
                cell_list[row_number * 10 + 4].value = product["pa"]

                cell_list[row_number * 10 + 5].value = product["original_price"]
                cell_list[row_number * 10 + 6].value = product["price"]

                cell_list[row_number * 10 + 7].value = product["qty"]
                cell_list[row_number * 10 + 8].value = (
                    "=G" + str(row_number + 1) + "*H" + str(row_number + 1)
                )
                cell_list[row_number * 10 + 9].value = (
                    "=CEILING(IF(LEN(E"
                    + str(row_number + 1)
                    + ")=8,I"
                    + str(row_number + 1)
                    + ",0.95*I"
                    + str(row_number + 1)
                    + "),0.01)"
                )
                row_number += 1

            last_row = row_number - 1

            cell_list[row_number * 10 + 8].value = (
                "=SUM(I" + str(first_row + 1) + ":I" + str(last_row + 1) + ")"
            )
            cell_list[row_number * 10 + 9].value = (
                "=SUM(J" + str(first_row + 1) + ":J" + str(last_row + 1) + ")"
            )

            summary.append(
                (user, "=SUM(J" + str(first_row + 1) + ":J" + str(last_row + 1) + ")")
            )

            row_number += 2

    start_row_total_sum = row_number + 1
    for user_sum in summary:
        cell_list[row_number * 10].value = user_sum[0]
        cell_list[row_number * 10 + 1].value = user_sum[1]
        row_number += 1
    end_row_total_sum = row_number

    row_number += 1

    cell_list[row_number * 10].value = "Totaal"
    cell_list[row_number * 10 + 1].value = (
        "=SUM(B" + str(start_row_total_sum) + ":B" + str(end_row_total_sum) + ")"
    )
    row_number += 1

    cell_list[row_number * 10].value = "zonder 5%"
    cell_list[row_number * 10 + 1].value = "=B" + str((row_number)) + "/0.95"
    row_number += 1

    cell_list[row_number * 10].value = "Met porto"
    cell_list[row_number * 10 + 1].value = "=B" + str((row_number)) + "+5.95"
    row_number += 1

    # TODO: return cells and add them in another function to the worksheet
    worksheet.update_cells(cell_list, value_input_option="USER_ENTERED")

    print("Orders added to spreadsheet")
