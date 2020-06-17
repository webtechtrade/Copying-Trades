import logging

import telegram

from configuration import Configuration


class MessageHelper:
    def __init__(self):
        configuration = Configuration()
        self.token_bot = configuration.config['TELEGRAM']['BOT_TOKEN']
        self.chat_id = configuration.config['TELEGRAM']['CHAT_ID']
        self.bot = telegram.Bot(self.token_bot)
        self.message_queue = []

    def send_notify(self, message):
        """
            Сделаем когда нибудь его асинхронным
        :param message:
        :return:
        """
        logging.info(message)
        try:
            self.message_queue.append(message)
        except Exception as ex:
            logging.error(ex)

    def check_queue(self):
        try:
            while self.message_queue:
                message = self.message_queue.pop()
                self.bot.send_message(self.chat_id, message, parse_mode=telegram.parsemode.ParseMode.HTML)
        except Exception as ex:
            logging.error(ex)
