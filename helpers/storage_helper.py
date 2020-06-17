import asyncio
import copy
import datetime
from typing import List

from helpers.message_helper import MessageHelper
from models.actual_transactions import ActualTransactions
from models.storage_models.client_transaction import ClientTransaction
from models.storage_models.standard_transaction import StandardTransaction
from services.storage_service import StorageService


class StorageHelper:
    def __init__(self, message_helper):
        self.storage_service = StorageService()
        self.message_helper = message_helper

    def add_new_transaction(self, transactions: List[StandardTransaction]):
        """
            Проверяем есть ли новые транзации, и возвращаем только новые
        :param transaction:
        :return:
        """
        # Запрос к СУБД на предмет новых транзакций
        session = self.storage_service.create_session()

        for item in transactions:
            db_item = session.query(StandardTransaction).filter_by(orderID=item.orderID).first()
            if not db_item:
                # Добавить в хранилище
                session.add(item)
                self.message_helper.send_notify("New transaction: \n" + item.to_telegram_str())

            elif db_item.ordStatus == "Filled":
                # Пропускаем транзацкию если она завершена
                continue

            elif db_item.ordStatus == "Canceled":
                # Пропускаем транзацкию если она завершена
                continue
            else:
                if item.ordStatus != db_item.ordStatus:
                    session.query(StandardTransaction).filter_by(orderID=item.orderID).\
                        update({"ordStatus": item.ordStatus, "read_status": 0})
                    self.message_helper.send_notify("New status: \n" + item.to_telegram_str())

                    if item.ordStatus == "Filled":
                        # Обновляем время завершения транзацкии что бы отчет таймера выполнить
                        self.time_filled_client_update(session, item.orderID)

        session.commit()
        session.close()

    def read_transactions(self) -> List[StandardTransaction]:
        session = self.storage_service.create_session()
        unread_transaction = session.query(StandardTransaction).filter_by(read_status=0).all()
        for item in unread_transaction:
            session.query(StandardTransaction).filter_by(orderID=item.orderID). \
                update({"read_status": 1})
        read_transaction = copy.deepcopy(unread_transaction)
        session.commit()
        session.close()
        return read_transaction

    def add_order(self, order: ClientTransaction):
        session = self.storage_service.create_session()
        session.add(order)
        session.commit()
        session.close()

    def update_client_transaction(self, transactions:List[StandardTransaction]):
        # Запрос к СУБД на предмет новых транзакций
        session = self.storage_service.create_session()
        # storage_transactions = session.query(Transaction).filter(Transaction.orderID.in_(array_orders)).all()
        for item in transactions:
            db_item = session.query(ClientTransaction).filter_by(orderID=item.orderID).first()
            if not db_item:
                pass
            else:
                if item.ordStatus != db_item.ordStatus:
                    session.query(ClientTransaction).filter_by(orderID=item.orderID). \
                        update({"ordStatus": item.ordStatus})
                    self.message_helper.send_notify("New status: \n" + item.to_telegram_str())
        session.commit()
        session.close()

    def get_client_order_by_reference(self, orderID_reference):
        result = []
        session = self.storage_service.create_session()
        transactions = session.query(ClientTransaction).filter_by(orderID_reference=orderID_reference).all()
        for item in transactions:
            result.append(item.orderID)
        return result

    def is_time_up(self, orderID):
        session = self.storage_service.create_session()
        transaction = session.query(ClientTransaction).filter_by(orderID=orderID).first()
        if not transaction:
            return False
        if transaction.time_up == 1:
            return False
        else:
            return True

    def get_client_order(self, orderID)->ClientTransaction:
        session = self.storage_service.create_session()
        transaction = session.query(ClientTransaction).filter_by(orderID=orderID).first()
        session.expunge_all()
        return transaction

    def time_up_completed(self, orderID):
        session = self.storage_service.create_session()
        session.query(ClientTransaction).filter_by(orderID=orderID). \
            update({"time_up": 1})
        session.commit()
        session.close()

    def time_filled_client_update(self, session, orderID_reference):
        time_filled_reference = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        session.query(ClientTransaction).filter_by(orderID_reference=orderID_reference). \
            update({"time_filled_reference": time_filled_reference})
