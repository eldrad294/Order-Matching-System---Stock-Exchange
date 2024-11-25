from sortedcontainers import SortedKeyList
from enum import Enum
from datetime import datetime
import hashlib, math

class Stock:
    """
    Defines the Stock payload.
    Stock is the trading unit that can be 'bought' or 'sold'.
    """

    def __init__(self, id: int, name: str, price: float):
        """
        Class Initializer
        :param id: Unique identifier for the stock.
        :param name: Stock label / name.
        :param price: The base value amount for the stock.
        """
        self.id = id
        self.name = name
        self.price = price


class Order:
    """
    Defines the Order payload.
    An order constitutes a stock item, the amount of it being ordered,
    whether it's being purchased or sold, and the time fields of the order.
    """

    class OrderAction(Enum):
        BUY = 1
        SELL = 2

    class OrderStatus(Enum):
        OPEN = 1
        FILLED = 2
        PARTIAL_FILL = 3

    def __init__(self, stock: Stock, ordered_quantity: int, action: OrderAction, user_id: str):
        """
        Class Initializer
        :param stock: The stock being ordered.
        :param ordered_quantity: The number of stock items being ordered. Partial orders are not supported in this
               use-case.
        :param action: Whether the order is for a purchase, or sale.
        :param status: The status of the order. In the beginning, every order defaults to being OPEN.
        :param user_id: A unique identifier which signifies the author / owner of the order. This can be either a
                        uniquely generated string created at user creation level, or perhaps an email address (which
                        should be unique per user).

        Furthermore, the model supports the following fields, which are used throughout the lifetime of the model, but
        are initialized always with the same defaults.
        :param created: The datetime when the order was marked as OPEN
        :param order_id: The unique identifier of the order. In this usecase, we calculate a hash from the order's
                         content.
        :param current_quantity: The number of stock items currently marked within the order. When the order is brand
                         new, the current_quantity will always match the ordered_quantity.
        :param status: The status of the order, which always starts as OPEN
        :param settled: The datetime when the order was marked as FILLED
        :param last_status_update: The datetime with when the order was last modified
        """
        self.stock = stock
        self.ordered_quantity = ordered_quantity
        self.action = action
        self.user_id = user_id

        self.created = datetime.now()
        self.order_id = hashlib.md5(
            f"{stock.id}{ordered_quantity}{action}{user_id}{self.created}".encode('utf-8')).hexdigest()
        self.current_quantity = ordered_quantity
        self.status = self.OrderStatus.OPEN.value
        self.settled = None
        self.last_status_update = datetime.now()


class OrderBook:
    """
    An OrderBook class signifies a traditional order book in an order matching system.
    It is composed of 2 sorted dictionary data structures, which track the buy & sell orders respectively.
    """

    def __init__(self):
        """
        Class Initializer.
        """
        self.buy_orders = SortedKeyList(key=lambda order: order.stock.price)
        self.sell_orders = SortedKeyList(key=lambda order: order.stock.price)


class Trade:
    """
    A trade class which tracks every single trade transaction within the order book
    """

    def __init__(self, stock_id: int, best_buy_order_id: str, best_sell_order_id: str, trade_price: float,
                 quantity: int, timestamp: datetime):
        """
        Class Initializer.
        :param stock_id: int, denoting the id of the stock present in the trade.
        :param best_buy_order_id: str, denoting the id of the BUY order.
        :param best_sell_order_id: str, denoting the id of the SALE order.
        :param trade_price: flt, denoting the price of the stock within the trade.
        :param quantity: int, denoting the amount of stock being traded.
        :param timestamp: datetime, denoting the time of the trade.
        """
        self.stock_id = stock_id
        self.best_buy_order_id = best_buy_order_id
        self.best_sell_order_id = best_sell_order_id
        self.trade_price = trade_price
        self.quantity = quantity
        self.timestamp = timestamp


class OrderSystem:
    """
    Main class, which tracks all OrderBooks and Orders within, as an OrderSystem.
    Exposes methods with which to interact with the OrderSystem.
    """

    def __init__(self):
        """
        Class Initializer.
        """
        self.order_system = {}

    def add_order(self, order: Order) -> (bool, str):
        """
        Routine which handles creation of an order.
        :param order: An object of type 'Order'
        :return: Tuple, denoting the response code (True if succeeded, False if not) & message from the function.
        """
        order_system_key = order.stock.id

        # Initializer for new stocks not registered on the OrderSystem
        if order_system_key not in self.order_system.keys():
            self.order_system[order_system_key] = OrderBook()

        # Adds the order on the appropriate OrderBook
        if order.action == Order.OrderAction.BUY.value:
            self.order_system[order_system_key].buy_orders.add(order)
            response_msg = (True, f"Purchase order successfully added")
        elif order.action == Order.OrderAction.SELL.value:
            self.order_system[order_system_key].sell_orders.add(order)
            response_msg = (True, f"Sale order successfully added")
        else:
            response_msg = (False, f"Unsupported order action, received: {order.action}")
        return response_msg

    def match_orders(self) -> list:
        """
        Reconciles all OrderBooks within the OrderSystem, by matching the BUY & SALE ledger. The comparison is done by
        taking the end order within the SALE OrderBook (highest sale), and the taking the first order within the BUY
        OrderBook (lowest purchase). The difference / delta between the two Order amounts is subtracted from either
        booking. If that amount reaches 0, that booking is considered FILLED, and settled. If that amount does not reach
        0, that booking is considered as PARTIALLY_FILLED, and remains open for future matching. Every iteration of this
        is recorded as a trade for audit purposes.
        :return: List of Trades, which denote the specifics of the exchange between stock.
        """
        trades = []  # List to store executed trades
        for stock_id, order_book in self.order_system.items():
            try:
                best_sell_order = order_book.sell_orders[-1]
                best_buy_order = order_book.buy_orders[0]
            except IndexError:
                print("Insufficient orders to trade.")
                return trades

            delta = best_buy_order.current_quantity - best_sell_order.current_quantity
            sell_order = order_book.sell_orders.pop(-1)
            buy_order = order_book.buy_orders.pop(0)

            if delta > 0:
                buy_order.current_quantity = delta
                buy_order.status = Order.OrderStatus.PARTIAL_FILL
                buy_order.last_status_update = datetime.now()
                sell_order.current_quantity = 0
                sell_order.status = Order.OrderStatus.FILLED
                sell_order.last_status_update = datetime.now()
                sell_order.settled = datetime.now()
                self.add_order(buy_order)
            elif delta < 0:
                sell_order.current_quantity = math.sqrt(delta ** 2)
                sell_order.status = Order.OrderStatus.PARTIAL_FILL
                sell_order.last_status_update = datetime.now()
                buy_order.current_quantity = 0
                buy_order.status = Order.OrderStatus.FILLED
                buy_order.last_status_update = datetime.now()
                buy_order.settled = datetime.now()
                self.add_order(sell_order)
            else:  # When orders match exactly in quantity
                buy_order.current_quantity, sell_order.current_quantity = 0, 0
                buy_order.status, sell_order.status = Order.OrderStatus.FILLED, Order.OrderStatus.FILLED
                buy_order.last_status_update, sell_order.last_status_update = datetime.now(), datetime.now()
                buy_order.settled, sell_order.settled = datetime.now(), datetime.now()
            trades.append(
                Trade(
                    stock_id=stock_id,
                    best_buy_order_id=buy_order.order_id,
                    best_sell_order_id=sell_order.order_id,
                    trade_price=sell_order.stock.price,
                    quantity=int(math.sqrt(delta ** 2)),
                    timestamp=datetime.now()
                )
            )
        return trades

    def get_order_system(self) -> dict:
        """
        Retrieves the OrderSystem as a dictionary.
        :return: The OrderSystem, and all its OrderBooks
        """
        return self.order_system

    def get_order_book(self, stock_id: int) -> OrderBook:
        """
        Retrieves the order book for a particular stock
        :param stock_id: Int, denoting the stock id parameter.
        :return: A specific OrderBook, and all its orders
        """
        return self.order_system[stock_id]
