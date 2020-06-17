from . import DeclarativeBase
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float


class ClientTransaction(DeclarativeBase):
    __tablename__ = 'client_transactions'
    orderID = Column(String, primary_key=True, nullable=False)
    orderID_reference = Column(String(100))
    account_name = Column(String(100))
    account = Column(Integer)
    side = Column(String(100))
    currency = Column(String(100))
    price = Column(Float)
    transactTime = Column(String)
    timestamp = Column(String)
    ordStatus = Column(String)
    orderQty = Column(String)
    ordType = Column(String)
    stopPx = Column(String)
    execInst = Column(String)
    time_up = Column(Integer, default=0)
    time_filled_reference = Column(String)

    def to_telegram_str(self) -> str:
        return ("OrderID: %s \n Account: %s \n Price: %s\n OrderQty: %s\n"
                " Status: %s\n Order Type: %s\n Stop Price: %s\n Expanded: %s\n TimeStamp: %s" % (
                    self.orderID, self.account_name, self.price, self.orderQty,
                    self.ordStatus, self.ordType, self.stopPx, self.execInst, self.transactTime)).replace("None", " - ")
