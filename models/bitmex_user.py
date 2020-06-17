import datetime
import logging
import math
from typing import List

import asyncio
import bitmex

from helpers.message_helper import MessageHelper
from helpers.storage_helper import StorageHelper
from models.storage_models.client_transaction import ClientTransaction
from models.storage_models.standard_transaction import StandardTransaction


class BitmexUser:
    def __init__(self, is_test, name, api_url, api_key, api_secret, time_to_cancel, percent_price, multiplier_quantity,
                 time_to_up, message_helper):
        self.name = name
        self.api_url = api_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.is_test = is_test
        from api.bitmex_websocket import BitMEXWebsocket
        self.ws = BitMEXWebsocket(endpoint=self.api_url, symbol="XBTUSD", api_key=self.api_key,
                                  api_secret=self.api_secret)
        self.message_helper = message_helper
        self.storage_helper = StorageHelper(message_helper)
        self.web_api = bitmex.bitmex(api_key=api_key, api_secret=api_secret, test=is_test)
        self.time_to_cancel = time_to_cancel
        self.time_to_up_price = time_to_up
        self.percent_price = percent_price
        self.multiplier_quantity = multiplier_quantity
        self.message_helper.send_notify("Start client:" + self.to_telegram_str())

    def to_telegram_str(self):
        mode = "PRODUCTION"
        if self.is_test:
            mode = "TEST"
        return "\n MODE: %s \n NAME: %s\n MULTIPLIER_QUANTITY: %s" % (mode, self.name, str(self.multiplier_quantity))

    def actual_operations(self) -> List[StandardTransaction]:
        result_list = []

        array_orders = self.ws.orders()
        for order in array_orders:
            transaction = StandardTransaction()
            transaction.account = order["account"]
            transaction.currency = order["currency"]
            transaction.orderID = order["orderID"]
            transaction.price = order["price"]
            transaction.side = order["side"]
            transaction.timestamp = order["timestamp"]
            transaction.transactTime = order["transactTime"]
            transaction.ordStatus = order["ordStatus"]
            transaction.orderQty = order["orderQty"]
            transaction.ordType = order["ordType"]
            transaction.stopPx = order["stopPx"]
            transaction.execInst = order['execInst']
            transaction.account_name = self.name
            result_list.append(transaction)
        return result_list

    @staticmethod
    def convert_datetime(raw_date)->datetime:
        try:
            return datetime.datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        except TypeError:
            return None
