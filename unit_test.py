import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from parking_lot.src.slots import Slots
from parking_lot.src.admin import Admin 
from parking_lot.src.parking_gate_system import ParkingGateSystem 
from parking_lot.src.user import User

class TestSlots(unittest.TestCase):

    @patch('sqlite3.connect')
    def setUp(self, mock_connect):
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        mock_connect.return_value = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor
        self.slots = Slots()

    def test_return_all_available_slots(self):
        self.mock_cursor.fetchall.return_value = [(1,), (2,)]
        available_slots = self.slots.return_all_available_slots()
        self.assertEqual(available_slots, [(1,), (2,)])
        self.mock_cursor.execute.assert_called_with('SELECT slot_number FROM parking_slots WHERE status="free"')

    def test_book_slot(self):
        self.mock_cursor.rowcount = 1
        self.slots.book_slot(1)
        self.mock_cursor.execute.assert_called_with('''
            UPDATE parking_slots 
            SET status="occupied" 
            WHERE slot_number=? AND status="free"
        ''', (1,))
        self.mock_conn.commit.assert_called_once()

    def test_book_slot_error(self):
        self.mock_cursor.rowcount = 0
        with self.assertRaises(ValueError):
            self.slots.book_slot(1)

    def test_release_slot(self):
        self.mock_cursor.rowcount = 1
        self.slots.release_slot(1)
        self.mock_cursor.execute.assert_called_with('''
            UPDATE parking_slots 
            SET status="free" 
            WHERE slot_number=? AND status="occupied"
        ''', (1,))
        self.mock_conn.commit.assert_called_once()

    def test_release_slot_error(self):
        self.mock_cursor.rowcount = 0
        with self.assertRaises(ValueError):
            self.slots.release_slot(1)

    def test_return_all_occupied_slots(self):
        self.mock_cursor.fetchall.return_value = [(1,), (2,)]
        occupied_slots = self.slots.return_all_occupied_slots()
        self.assertEqual(occupied_slots, [(1,), (2,)])
        self.mock_cursor.execute.assert_called_with('SELECT slot_number FROM parking_slots WHERE status="occupied"')

    def tearDown(self):
        self.slots.close_connection()


class TestAdmin(unittest.TestCase):

    @patch('sqlite3.connect')
    def setUp(self, mock_connect):
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        mock_connect.return_value = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor
        self.admin = Admin()

    def test_get_prices(self):
        self.mock_cursor.fetchall.return_value = [('car', 10), ('bike', 5)]
        prices = self.admin.get_prices()
        self.assertEqual(prices, [('car', 10), ('bike', 5)])
        self.mock_cursor.execute.assert_called_with("SELECT * FROM parking_prices")

    def test_update_prices_new_vehicle(self):
        self.admin.get_prices = MagicMock(return_value=[('car', 10)])
        self.admin.update_prices('bike', 5)
        self.mock_cursor.execute.assert_called_with('INSERT INTO parking_prices VALUES (?,?);', ('bike', 5))
        self.mock_conn.commit.assert_called_once()

    def test_get_users_info(self):
        self.mock_cursor.fetchall.return_value = [(1, '2022-01-01', None, 'car', 1)]
        user_info = self.admin.get_users_info(1)
        self.assertEqual(user_info, [(1, '2022-01-01', None, 'car', 1)])
        self.mock_cursor.execute.assert_called_with("SELECT * FROM parking_tickets WHERE user_id = 1")

    def test_add_new_user(self):
        self.mock_cursor.fetchone.return_value = [1]
        new_user_id = self.admin.add_new_user(50.0)
        self.assertEqual(new_user_id, 2)
        self.mock_cursor.execute.assert_called_with("INSERT INTO user_data (user_id, amount) VALUES (?, ?);", (2, 50.0))
        self.mock_conn.commit.assert_called_once()


class TestUser(unittest.TestCase):

    @patch('sqlite3.connect')
    def setUp(self, mock_connect):
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        mock_connect.return_value = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor
        self.user = User(1)

    def test_get_balance(self):
        self.mock_cursor.fetchone.return_value = [100.0]
        balance = self.user.get_balance()
        self.assertEqual(balance, 100.0)
        self.mock_cursor.execute.assert_called_with("SELECT amount FROM user_data WHERE user_id = 1;")

    def test_get_all_history(self):
        self.mock_cursor.fetchall.return_value = [(1, '2022-01-01', None, 'car', 1)]
        history = self.user.get_all_history()
        self.assertEqual(history, [(1, '2022-01-01', None, 'car', 1)])
        self.mock_cursor.execute.assert_called_with("SELECT * FROM parking_tickets WHERE user_id = 1")

    def test_add_balance(self):
        self.mock_cursor.fetchone.return_value = [100.0]
        self.user.add_balance(50.0)
        self.mock_cursor.execute.assert_called_with("UPDATE user_data SET amount = 150.0 WHERE user_id = 1;")
        self.mock_conn.commit.assert_called_once()


class TestParkingGateSystem(unittest.TestCase):

    @patch('sqlite3.connect')
    def setUp(self, mock_connect):
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        mock_connect.return_value = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor
        self.gate_system = ParkingGateSystem()

    def test_get_price(self):
        self.mock_cursor.fetchone.return_value = [60]
        net_time = timedelta(minutes=10)
        price = self.gate_system.get_price(net_time, 'car')
        self.assertEqual(price, 60.0)
        self.mock_cursor.execute.assert_called_with("SELECT amount FROM parking_prices WHERE vehicle_type = ?", ('car',))

    def test_add_out_time(self):
        self.mock_cursor.fetchone.side_effect = [
            ('2022-01-01 12:00:00', 1, 'car'),
            [60]
        ]
        price = self.gate_system.add_out_time(1)
        self.assertEqual(price, 60.0)
        self.mock_cursor.execute.assert_called_with("UPDATE parking_tickets SET out_time = ? WHERE ticket_id = ? AND out_time IS NULL;", (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1))
        self.mock_conn.commit.assert_called_once()
        self.mock_cursor.execute.assert_called_with("SELECT in_time, slot, vehicle_type FROM parking_tickets WHERE ticket_id = ?;", (1,))

    def test_show_free_slots(self):
        self.gate_system.slots_manager.return_all_available_slots = MagicMock(return_value=[(1,), (2,)])
        free_slots = self.gate_system.show_free_slots()
        self.assertEqual(free_slots, [(1,), (2,)])

    def test_create_new_ticket(self):
        self.gate_system.slots_manager.return_all_available_slots = MagicMock(return_value=[(1,)])
        ticket_id = self.gate_system.create_new_ticket(1, 'car')
        self.assertIsNotNone(ticket_id)
        self.mock_cursor.execute.assert_called_with("INSERT INTO parking_tickets (user_id, in_time, out_time, vehicle_type, slot) VALUES (?, ?, NULL, ?, ?);", (1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'car', 1))
        self.mock_conn.commit.assert_called_once()
        self.gate_system.slots_manager.book_slot.assert_called_once_with(1)

if __name__ == '__main__':
    unittest.main(argv=[''], verbosity=2, exit=False)
