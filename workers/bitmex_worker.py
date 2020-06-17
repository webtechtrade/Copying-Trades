import json
import logging
import threading
import time
from typing import List

import asyncio

from configuration import Configuration

from helpers.message_helper import MessageHelper
from helpers.storage_helper import StorageHelper
from models.bitmex_user import BitmexUser
from models.bitmex_user_client import BitmexUserClient


class BitmexWorker:
    def __init__(self):
        configuration = Configuration()
        self.message_helper = MessageHelper()
        self.is_test = configuration.config["IS_TEST"]

        self.clients = []
        self.init_clients()

        self.th_check_reference = threading.Thread(target=self.do_check_reference)
        self.th_check_reference.daemon = True

        self.th_eval_client = threading.Thread(target=self.do_eval_client)
        self.th_eval_client.daemon = True

        self.th_check_client = threading.Thread(target=self.do_check_client)
        self.th_check_client.daemon = True

        self.th_check_new_client = threading.Thread(target=self.do_check_new_client)
        self.th_check_new_client.daemon = True

        self.th_check_client_up = threading.Thread(target=self.do_check_client_up)
        self.th_check_client_up.daemon = True

        self.th_message_send = threading.Thread(target=self.do_message_send)
        self.th_message_send.daemon = True

        self.bitmex_reference = BitmexUser(self.is_test, "Reference",
                                           configuration.config["URL_API"],
                                           configuration.config['REFERENCE']['API_KEY'],
                                           configuration.config['REFERENCE']['API_SECRET'], 0, 0, 1, 0, self.message_helper)
        self.storage_helper = StorageHelper(self.message_helper)

    def init_clients(self):
        """
            Пройдем по всем клиентам и добавим в массив
        :return:
        """
        configuration = Configuration()
        client_cfg = configuration.config['CLIENTS']

        for cl in client_cfg:
            client = BitmexUserClient(self.is_test, cl["NAME"], configuration.config["URL_API"], cl["API_KEY"],
                                      cl["API_SECRET"],
                                      configuration.config["TIME_TO_CANCEL"], configuration.config["PERCENT_PRICE"],
                                      cl["MULTIPLIER_QUANTITY"], configuration.config["TIME_TO_UP"], self.message_helper)
            self.clients.append(client)

    def start(self):
        self.th_check_reference.start()
        self.th_eval_client.start()
        self.th_check_client.start()
        self.th_check_new_client.start()
        self.th_check_client_up.start()
        self.th_message_send.start()

    def do_check_reference(self):
        logging.info("Starting check_reference...")
        try:
            while True:
                self.check_reference()
                time.sleep(0.05)
        except Exception as ex:
            self.message_helper.send_notify("Error check_reference:\n" + str(ex))

    def do_eval_client(self):
        logging.info("Starting eval_client...")
        try:
            while True:
                self.eval_client()
                time.sleep(0.05)
        except Exception as ex:
            self.message_helper.send_notify("Error eval_client:\n" + str(ex))

    def do_check_client(self):
        logging.info("Starting check_client...")
        try:
            while True:
                self.check_active_order_client()
                time.sleep(0.05)
        except Exception as ex:
            self.message_helper.send_notify("Error check_client:\n" + str(ex))

    def do_check_new_client(self):
        logging.info("Starting check_new_client...")
        try:
            while True:
                self.check_new_order_client()
                time.sleep(0.05)
        except Exception as ex:
            self.message_helper.send_notify("Error check_new_client:\n" + str(ex))

    def do_check_client_up(self):
        logging.info("Starting do_check_client_up...")
        try:
            while True:
                self.check_client_up()
                time.sleep(0.05)
        except Exception as ex:
            self.message_helper.send_notify("Error do_check_client_up:\n" + str(ex))

    def do_message_send(self):
        logging.info("Starting do_message_send...")
        try:
            while True:
                self.message_helper.check_queue()
                time.sleep(1)
        except Exception as ex:
            self.message_helper.send_notify("Error do_message_send:\n" + str(ex))

    def check_reference(self):
        """
            Будем вызывать при каждой новой операции
        """
        ref_operation = self.bitmex_reference.actual_operations()
        logging.debug(ref_operation)

        if not ref_operation:
            logging.debug("Order is empty")
            return

        # Проверяем операции с локальной БД для эталона, а есть ли новые
        self.storage_helper.add_new_transaction(ref_operation)

    def eval_client(self):
        """
            Получим непрочитанные сделки, и выставим новые счета
        :return:
        """
        unread_transactions = self.storage_helper.read_transactions()
        logging.debug(unread_transactions)
        # у всех клиентов запустим сделки
        for client in self.clients:
            client.make_operations(unread_transactions)

    def check_active_order_client(self):
        """
            Проверяем завершенные сделки, их успех или неудачу, рассылаем уведомления
        :return:
        """
        for client in self.clients:
            orders = client.actual_operations()
            if not orders:
                continue
            self.storage_helper.update_client_transaction(orders)

    def check_new_order_client(self):
        """
            Проверяем открыте ордера, и завершаем если не прошел
        :return:
        """
        for client in self.clients:
            client.cancel_operations_time()

    def check_client_up(self):
        """
            Через заданый интервал поднимаем или меняем цену
        :return:
        """
        for client in self.clients:
            client.update_price_time()

