from fastapi import FastAPI, status, Response
from pydantic import BaseModel
from typing import List
from engine import OrderSystem, OrderBook, Order, Stock

app = FastAPI()
order_system = OrderSystem()

class StockModel(BaseModel):
    id: int
    name: str
    price: float

class OrderModel(BaseModel):
    stock: StockModel
    ordered_quantity: int
    action: int
    user_id: str
    created: str | None = None
    order_id: str | None = None
    current_quantity: int | None = None
    status: int | None = None
    settled: str | None = None
    last_status_update: str | None = None

class OrderBookModel(BaseModel):
    buy_orders: list[OrderModel] | None = None
    sell_orders: list[OrderModel] | None = None

class TradeModel(BaseModel):
    stock_id: int
    best_buy_order_id: str
    best_sell_order_id: str
    trade_price: float
    quantity: int
    timestamp: str

class OrderSystemModel(BaseModel):
    order_system: dict[int, OrderBookModel] = {}

@app.get("/")
async def entry():
    return {"message": "Ready."}


@app.post("/order/create", response_model=str, status_code=status.HTTP_201_CREATED)
async def create_order(order_model: OrderModel, response: Response):
    """
    Order creation endpoint.
    """
    print(f"-> Received order request {order_model}")
    stock = Stock(
        id=order_model.stock.id,
        name=order_model.stock.name,
        price=order_model.stock.price
    )
    order = Order(
        stock=stock,
        ordered_quantity=order_model.ordered_quantity,
        action=order_model.action,
        user_id=order_model.user_id
    )
    engine_response = order_system.add_order(order)
    print(engine_response[1])
    if not engine_response[0]:
        response.status_code = status.HTTP_400_BAD_REQUEST
    return engine_response[1]


def __order_mapper(order: Order) -> OrderModel:
    """
    Mapper function, to help with mapping engine class to FastAPI REST model
    :param order: Order details
    :return: Rest Template Model
    """
    stock_model = StockModel(
        id=order.stock.id,
        name=order.stock.name,
        price=order.stock.price
    )
    order_model = OrderModel(
        stock=stock_model,
        ordered_quantity=order.ordered_quantity,
        action=order.action,
        user_id=order.user_id,
        created=str(order.created),
        order_id=str(order.order_id),
        current_quantity=order.current_quantity,
        status=order.status,
        settled=str(order.settled),
        last_status_update=str(order.last_status_update)
    )
    return order_model

@app.get("/order/get_order_book/{stock_id}", response_model=OrderBookModel, status_code=status.HTTP_200_OK)
async def get_order_book(stock_id: str, response: Response):
    """
    Retrieve OrderBook for specific stock.
    """
    try:
        order_book = order_system.get_order_book(int(stock_id))

        order_purchases = [__order_mapper(order) for order in order_book.buy_orders]
        order_sales = [__order_mapper(order) for order in order_book.sell_orders]

        order_book_model = OrderBookModel(
            buy_orders=order_purchases,
            sell_orders=order_sales
        )
    except KeyError:
        response.status_code = status.HTTP_404_NOT_FOUND
        order_book_model = OrderBookModel()
    return order_book_model

@app.get("/order/get_order_system", response_model=OrderSystemModel, status_code=status.HTTP_200_OK)
async def get_order_system():
    """
    Retrieve OrderSystem.
    """
    os = order_system.get_order_system()
    order_system_model = OrderSystemModel()
    for stock_id, order_book in os.items():
        order_purchases = [__order_mapper(order) for order in order_book.buy_orders]
        order_sales = [__order_mapper(order) for order in order_book.sell_orders]
        order_book_model = OrderBookModel(
            buy_orders=order_purchases,
            sell_orders=order_sales
        )
        order_system_model.order_system[stock_id] = order_book_model
    return order_system_model


@app.patch("/order/match_orders", response_model=List[TradeModel], status_code=status.HTTP_200_OK)
async def match_orders():
    """
    Matches the orders and executes trades
    """
    trades_list = order_system.match_orders()
    trades_model_list = []
    for trade in trades_list:
        trade_model = TradeModel(
           stock_id=trade.stock_id,
           best_buy_order_id=trade.best_buy_order_id,
           best_sell_order_id=trade.best_sell_order_id,
           trade_price=trade.trade_price,
           quantity=trade.quantity,
           timestamp=str(trade.timestamp)
        )
        trades_model_list.append(trade_model)
    return trades_model_list
