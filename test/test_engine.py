import unittest
from src.engine import OrderSystem, Stock, Order


class TestOrderSystem(unittest.TestCase):
    def setUp(self):
        self.order_system = OrderSystem()
        self.stock = Stock(1,'DummyStock', 100)

    def test_add_order_buy(self):
        order = Order(self.stock, 1, Order.OrderAction.BUY.value, "1234")
        response = self.order_system.add_order(order)
        self.assertTrue(response[0])
        self.assertIn(1, self.order_system.get_order_system())
        self.assertEqual(len(self.order_system.get_order_book(1).buy_orders), 1)

    def test_add_order_sell(self):
        order = Order(self.stock, 2, Order.OrderAction.SELL.value, "1234")
        response = self.order_system.add_order(order)
        self.assertTrue(response[0])
        self.assertIn(1, self.order_system.get_order_system())
        self.assertEqual(len(self.order_system.get_order_book(1).sell_orders), 1)

    def test_add_order_invalid_action(self):
        order = Order(self.stock, 3, "INVALID", "1234")
        response = self.order_system.add_order(order)
        self.assertFalse(response[0])
        self.assertIn("Unsupported order action", response[1])

    def test_match_orders_full_match(self):
        buy_order = Order(self.stock, 4, Order.OrderAction.BUY.value, "1234")
        sell_order = Order(self.stock, 5, Order.OrderAction.SELL.value, "1234")
        self.order_system.add_order(buy_order)
        self.order_system.add_order(sell_order)

        trades = self.order_system.match_orders()
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].quantity, 1)
        self.assertEqual(trades[0].trade_price, self.stock.price)

    def test_match_orders_partial_fill(self):
        buy_order = Order(self.stock, 6, Order.OrderAction.BUY.value, "1234")
        sell_order = Order(self.stock, 7, Order.OrderAction.SELL.value, "1234")
        buy_order2 = Order(self.stock, 6, Order.OrderAction.BUY.value, "1234")
        self.order_system.add_order(buy_order)
        self.order_system.add_order(sell_order)
        self.order_system.add_order(buy_order2) # Do it again, to quantify remaining buy order after partial fill.

        trades = self.order_system.match_orders()
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].quantity, 1)
        self.assertEqual(trades[0].trade_price, self.stock.price)

        # Check remaining buy order
        remaining_buy_order = self.order_system.get_order_book(1).buy_orders[0]
        self.assertEqual(remaining_buy_order.current_quantity, 6)

    def test_match_orders_no_orders(self):
        trades = self.order_system.match_orders()
        self.assertEqual(len(trades), 0)

    def test_get_order_book(self):
        buy_order = Order(self.stock, 8, Order.OrderAction.BUY.value, "1234")
        self.order_system.add_order(buy_order)
        order_book = self.order_system.get_order_book(1)
        self.assertIsNotNone(order_book)
        self.assertEqual(len(order_book.buy_orders), 1)

    def test_get_order_system(self):
        self.assertEqual(len(self.order_system.get_order_system()), 0)
        buy_order = Order(self.stock, 9, Order.OrderAction.BUY.value, "1234")
        self.order_system.add_order(buy_order)
        self.assertEqual(len(self.order_system.get_order_system()), 1)

if __name__ == "__main__":
    unittest.main()