import asyncio
import datetime
import logging
import math
from typing import List

from models.bitmex_user import BitmexUser
from models.storage_models.client_transaction import ClientTransaction
from models.storage_models.standard_transaction import StandardTransaction


class BitmexUserClient(BitmexUser):

    def make_operations(self, unread_transactions: List[StandardTransaction]):
        """

        :param unread_transactions:
        :return:
        """

        for transaction in unread_transactions:
            try:
                # current_price = self.eval_price(transaction.price, transaction.side)
                if (transaction.ordStatus == "New") or (transaction.ordStatus == "Filled"):
                    self.create_transaction(transaction)

                elif transaction.ordStatus == "Canceled":
                    self.cancel_transaction(transaction)

            except Exception as ex:
                self.message_helper.send_notify("Error order " + self.name + ":\n" + str(ex))

    def cancel_operations_time(self):
        """
            Отменяем ордера у которых вышел таймаут
        :return:
        """
        cancel_order = []
        array_orders = self.ws.orders()
        for order in array_orders:
            if order['ordStatus'] == "New":
                transaction = self.storage_helper.get_client_order(order['orderID'])
                if transaction:
                    transactTime = BitmexUser.convert_datetime(transaction.time_filled_reference)
                    if transactTime:
                        if (transactTime + datetime.timedelta(minutes=self.time_to_cancel)) < datetime.datetime.utcnow():
                            cancel_order.append(order["orderID"])

        for order in cancel_order:
            try:
                self.web_api.Order.Order_cancel(orderID=order).result()
                msg = "Cancel order " + self.name + ":\n Order Id: " + order
                self.message_helper.send_notify(msg)

            except Exception as ex:
                self.message_helper.send_notify("Error cancel order " + self.name + ":\n" + str(ex))

    def eval_price(self, price, side):
        """
            При side Buy ниже прайса, равно и выше на процент покупаем
        :param price:
        :param side:
        :return:
        """
        result_price = price

        if side == "Buy":
            current_price = self.ws.get_instrument()["bidPrice"]
            if current_price <= price:
                result_price = price
            else:
                result_price = price + (price * self.percent_price)
        elif side == "Sell":
            current_price = self.ws.get_instrument()["askPrice"]
            if current_price >= price:
                result_price = price
            else:
                result_price = price - (price * self.percent_price)
        else:
            logging.error("Error operation")

        return self.round_of_rating(result_price)

    @staticmethod
    def round_of_rating(number):
        return round(number * 2) / 2

    def eval_quantity(self, orderQty):
        try:
            return math.ceil(int(orderQty) * self.multiplier_quantity)
        except ValueError:
            logging.error("Error orderQty %s" % orderQty)
            return None

    def create_transaction(self, transaction: StandardTransaction):
        curent_quantity = self.eval_quantity(transaction.orderQty)
        if transaction.ordType == "Limit":
            result = self.web_api.Order.Order_new(symbol='XBTUSD', orderQty=curent_quantity,
                                                  price=transaction.price, side=transaction.side,
                                                  ordType=transaction.ordType,
                                                  execInst=transaction.execInst
                                                  ).result()
        elif transaction.ordType == "Market":
            result = self.web_api.Order.Order_new(symbol='XBTUSD', orderQty=curent_quantity,
                                                  side=transaction.side,
                                                  ordType=transaction.ordType,
                                                  ).result()
        elif transaction.ordType == "Stop":
            result = self.web_api.Order.Order_new(symbol='XBTUSD', orderQty=curent_quantity,
                                                  side=transaction.side,
                                                  ordType=transaction.ordType,
                                                  stopPx=transaction.stopPx,
                                                  ).result()

        else:
            self.message_helper.send_notify(
                "Error order " + self.name + ":\n" + "Unknown type: " + transaction.ordType)
            return

        new_order = ClientTransaction()
        new_order.orderQty = result[0]['orderQty']
        new_order.orderID = result[0]['orderID']
        new_order.price = result[0]['price']
        new_order.side = result[0]['side']
        new_order.account = result[0]['account']
        new_order.timestamp = result[0]['timestamp']
        new_order.transactTime = result[0]['transactTime']
        new_order.ordStatus = result[0]['ordStatus']
        new_order.ordType = result[0]['ordType']
        new_order.stopPx = result[0]['stopPx']
        new_order.execInst = result[0]['execInst']
        new_order.account_name = self.name
        new_order.orderID_reference = transaction.orderID
        self.message_helper.send_notify(
            "New order client " + self.name + ":\n" + new_order.to_telegram_str())
        self.storage_helper.add_order(new_order)

    def cancel_transaction(self, transaction: StandardTransaction):
        """
            Необходимо найти все связанные транзации и отменить
        :param transaction:
        :return:
        """
        transactions = self.storage_helper.get_client_order_by_reference(transaction.orderID)
        for item in transactions:
            try:
                self.web_api.Order.Order_cancel(orderID=item).result()
                msg = "Cancel order " + self.name + ":\n Order Id: " + item
                self.message_helper.send_notify(msg)

            except Exception as ex:
                self.message_helper.send_notify("Error cancel order " + self.name + ":\n" + str(ex))

    def update_price_time(self):
        """
            По истечению времени если сделки не закрылись то апдейтим прайс
        :return:
        """
        update_order = []
        array_orders = self.ws.orders()
        for order in array_orders:
            if order['ordStatus'] == "New":
                transaction = self.storage_helper.get_client_order(order['orderID'])
                if transaction:
                    transactTime = BitmexUser.convert_datetime(transaction.time_filled_reference)
                    if transactTime:
                        if (transactTime + datetime.timedelta(minutes=self.time_to_up_price)) < datetime.datetime.utcnow():
                            update_order.append(transaction)

        for order in update_order:
            try:
                if order.time_up == 0:
                    current_price = self.eval_price(order.price, order.side)
                    self.web_api.Order.Order_amend(orderID=order.orderID, price=current_price).result()
                    msg = "Update order " + self.name + ":\n Order Id: " + order.orderID + "\nNew Price: " + \
                          str(current_price)
                    self.storage_helper.time_up_completed(order.orderID)
                    self.message_helper.send_notify(msg)

            except Exception as ex:
                self.message_helper.send_notify("Error Update order " + self.name + ":\n" + str(ex))


