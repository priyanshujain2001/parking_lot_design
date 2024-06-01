import sqlite3
import logging
from datetime import datetime
from paths import *
from src.slots import Slots
logging.basicConfig(level=logging.INFO, filename='logs\\parking_system.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
class ParkingGateSystem:
    """
    A class representing the parking gate system.

    Attributes:
        conn (sqlite3.Connection): Connection to the parking tickets database.
        cursor (sqlite3.Cursor): Cursor for executing SQL queries on the parking tickets database.
        slots_manager (Slots): An instance of the Slots class.
        users_db (sqlite3.Connection): Connection to the users database.
        cursor_users (sqlite3.Cursor): Cursor for executing SQL queries on the users database.
        parking_prices_db (sqlite3.Connection): Connection to the parking prices database.
        cursor_parking_prices (sqlite3.Cursor): Cursor for executing SQL queries on the parking prices database.
    """
    def __init__(self, parking_tickets=parking_tickets_path, users_db=users_db_path, parking_prices=parking_prices_path):
        """
        Initializes the ParkingGateSystem class.
        """
        try:
            self.conn = sqlite3.connect(parking_tickets)
            self.cursor = self.conn.cursor()
            self.slots_manager = Slots()
            self.users_db = sqlite3.connect(users_db)
            self.cursor_users = self.users_db.cursor()
            self.parking_prices_db = sqlite3.connect(parking_prices)
            self.cursor_parking_prices = self.parking_prices_db.cursor()
            logger.info("ParkingGateSystem connected to all databases")
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")

    def __del__(self):
        """
        Closes all database connections when the object is deleted.
        """
        try:
            self.conn.close()
            logger.info("ParkingGateSystem database connection closed")
        except sqlite3.Error as e:
            logger.error(f"Error closing database connection: {e}")

    def get_price(self, net_time, type_of_vehicle):
        """
        Calculates the price for parking based on vehicle type and duration.

        Args:
            net_time (datetime.timedelta): The duration of parking.
            type_of_vehicle (str): The type of vehicle.

        Returns:
            float: The calculated price for parking.
        """
        try:
            get_query = f"SELECT amount FROM parking_prices WHERE vehicle_type = ?"
            self.cursor_parking_prices.execute(get_query, (type_of_vehicle,))
            result = self.cursor_parking_prices.fetchone()[0]
            net_time_seconds = net_time.total_seconds()
            price = result * net_time_seconds / 3600  # Assuming price is per hour
            logger.info(f"Calculated price {price} for vehicle type {type_of_vehicle} and net time {net_time}")
            return price
        except sqlite3.Error as e:
            logger.error(f"Error calculating price: {e}")
            return 0.0

    def add_out_time(self, ticket_id):
        """
        Adds the out time for a parking ticket and calculates the price.

        Args:
            ticket_id (int): The ID of the parking ticket.

        Returns:
            float: The calculated price for parking.
        """
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            update_query = "UPDATE parking_tickets SET out_time = ? WHERE ticket_id = ? AND out_time IS NULL;"
            self.cursor.execute(update_query, (current_time, ticket_id))
            self.conn.commit()

            self.cursor.execute("SELECT in_time, slot, vehicle_type FROM parking_tickets WHERE ticket_id = ?;", (ticket_id,))
            result = self.cursor.fetchone()
            in_time = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
            out_time = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')

            self.slots_manager.release_slot(result[1])

            net_time = out_time - in_time
            price = self.get_price(net_time, result[2])
            logger.info(f"Added out time for ticket {ticket_id}. Calculated price is {price}")
            return price
        except sqlite3.Error as e:
            logger.error(f"Error adding out time: {e}")
            return 0.0

    def show_free_slots(self):
        """
        Retrieves all available parking slots.

        Returns:
            list: A list of available slot numbers.
        """
        try:
            slots = self.slots_manager.return_all_available_slots()
            logger.info("Retrieved available slots")
            return slots
        except Exception as e:
            logger.error(f"Error retrieving available slots: {e}")
            return []

    def create_new_ticket(self, user_id, vehicle_type):
        """
        Creates a new parking ticket for a user.

        Args:
            user_id (int): The ID of the user.
            vehicle_type (str): The type of vehicle.

        Returns:
            int: The ID of the newly created parking ticket.
        """
        try:
            free_slots = self.slots_manager.return_all_available_slots()
            if free_slots:
                user_id = int(user_id)
                free_slot = int(free_slots[0][0])
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                insert_query = "INSERT INTO parking_tickets (user_id, in_time, out_time, vehicle_type, slot) VALUES (?, ?, NULL, ?, ?);"
                self.cursor.execute(insert_query, (user_id, current_time, vehicle_type, free_slot))
                self.conn.commit()

                self.cursor.execute("SELECT last_insert_rowid();")
                new_ticket_id = self.cursor.fetchone()[0]

                self.slots_manager.book_slot(free_slot)
                logger.info(f"Created new ticket {new_ticket_id} for user {user_id} with vehicle type {vehicle_type} and slot {free_slot}")
                return new_ticket_id
            else:
                logger.warning("No empty slots available")
                return "No empty slots available"
        except sqlite3.Error as e:
            logger.error(f"Error creating new ticket: {e}")
            return None
