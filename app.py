from loggerinitializer import initialize_logger
from workers.bitmex_worker import BitmexWorker


def main():
    worker = BitmexWorker()
    worker.start()
    input()


if __name__ == '__main__':
    initialize_logger("log")
    main()

