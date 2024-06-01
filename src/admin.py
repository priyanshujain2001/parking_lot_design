import sqlite3
from datetime import datetime
from paths import *
from src.slots import Slots
import logging
import qrcode
# Configure the logger
logging.basicConfig(level=logging.INFO, filename='src\\logs\\admin.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



class Admin:
    """
    A class to manage administrative tasks related to parking.

    Attributes:
        users_db (sqlite3.Connection): Connection to the users database.
        cursor_users (sqlite3.Cursor): Cursor for executing SQL queries on the users database.
        parking_tickets_db (sqlite3.Connection): Connection to the parking tickets database.
        cursor_parking_ticket (sqlite3.Cursor): Cursor for executing SQL queries on the parking tickets database.
        parking_prices_db (sqlite3.Connection): Connection to the parking prices database.
        cursor_parking_prices (sqlite3.Cursor): Cursor for executing SQL queries on the parking prices database.
        slots_manager (Slots): An instance of the Slots class.
    """
    def __init__(self, users_db_name=users_db_path, parking_tickets=parking_tickets_path, parking_prices=parking_prices_path):
        """
        Initializes the Admin class.

        Args:
            users_db_name (str): The name of the users database file.
        """
        try:
            self.users_db = sqlite3.connect(users_db_name)
            self.cursor_users = self.users_db.cursor()
            self.parking_tickets_db = sqlite3.connect(parking_tickets)
            self.cursor_parking_ticket = self.parking_tickets_db.cursor()
            self.parking_prices_db = sqlite3.connect(parking_prices)
            self.cursor_parking_prices = self.parking_prices_db.cursor()
            self.slots_manager = Slots()
            logger.info("Admin connected to all databases")
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")

    def __del__(self):
        """
        Closes all database connections when the object is deleted.
        """
        try:
            self.users_db.close()
            self.parking_prices_db.close()
            self.parking_tickets_db.close()
            logger.info("All database connections closed")
        except sqlite3.Error as e:
            logger.error(f"Error closing database connection: {e}")

    def get_prices(self):
        """
        Retrieves parking prices from the database.

        Returns:
            list: A list of tuples containing vehicle types and their respective prices.
        """
        try:
            get_query = "SELECT * FROM parking_prices"
            self.cursor_parking_prices.execute(get_query)
            prices = self.cursor_parking_prices.fetchall()
            logger.info("Retrieved parking prices")
            return prices
        except sqlite3.Error as e:
            logger.error(f"Error retrieving prices: {e}")
            return []

    def update_prices(self, type_of_vehicle, new_price):
        """
        Updates parking prices in the database.

        Args:
            type_of_vehicle (str): The type of vehicle.
            new_price (float): The new price for the specified vehicle type.
        """
        try:
            vehicle_types = [i[0] for i in self.get_prices()]
            if type_of_vehicle not in vehicle_types:
                insert_query = 'INSERT INTO parking_prices VALUES (?,?);'
                self.cursor_parking_prices.execute(insert_query, (type_of_vehicle, new_price))
                self.parking_prices_db.commit()
                logger.info(f"Updated prices for vehicle type {type_of_vehicle} to {new_price}")
        except sqlite3.Error as e:
            logger.error(f"Error updating prices: {e}")

    def get_users_info(self, user_id):
        """
        Retrieves parking ticket information for a specific user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            list: A list of tuples containing parking ticket information for the specified user.
        """
        try:
            get_query = f"SELECT * FROM parking_tickets WHERE user_id = {user_id}"
            self.cursor_parking_ticket.execute(get_query)
            user_info = self.cursor_parking_ticket.fetchall()
            logger.info(f"Retrieved user info for user_id {user_id}")
            return user_info
        except sqlite3.Error as e:
            logger.error(f"Error retrieving user info: {e}")
            return []

    def get_available_slots(self):
        """
        Retrieves all available parking slots.

        Returns:
            list: A list of available slot numbers.
        """
        try:
            return self.slots_manager.return_all_available_slots()
        except Exception as e:
            logger.error(f"Error retrieving available slots: {e}")
            return []

    def get_all_occupied_slots(self):
        """
        Retrieves all occupied parking slots.

        Returns:
            list: A list of occupied slot numbers.
        """
        try:
            return self.slots_manager.return_all_occupied_slots()
        except Exception as e:
            logger.error(f"Error retrieving occupied slots: {e}")
            return []
        

    def add_user_to_database(self, user_id, name, email_id, phone_number):
        conn = sqlite3.connect('Databases\\user_data_personal.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE user_id=?", (user_id,))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"User ID {user_id} already exists in the database.")
        else:
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(user_id)
            qr.make(fit=True)
            
            img = qr.make_image(fill='black', back_color='white')
            qr_code_path = f'src\\qr_codes\\user_id_{user_id}.png'
            img.save(qr_code_path)
            cursor.execute(
            "INSERT INTO users (user_id, name, email_id, phone_number, qr_code_path) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, email_id, phone_number, qr_code_path))
            conn.commit()
            print(f"QR Code saved at: {qr_code_path}")
            conn.close()
            
    def add_new_user(self, name, email, phone_number, initial_balance):
        """
        Adds a new user to the system with an initial balance.

        Args:
            initial_balance (float): The initial balance for the new user.

        Returns:
            int: The ID of the new user.
        """
        try:
            self.cursor_users.execute("SELECT MAX(user_id) FROM user_data")
            max_user_id = self.cursor_users.fetchone()[0]
            new_user_id = max_user_id + 1 if max_user_id else 1
            qr_path = self.add_user_to_database(new_user_id,name, email, phone_number)
            insert_query = "INSERT INTO user_data (user_id, amount) VALUES (?, ?);"
            self.cursor_users.execute(insert_query, (new_user_id, initial_balance))
            self.users_db.commit()
            logger.info(f"Added new user with user_id {new_user_id} and initial balance {initial_balance}")
            
            return new_user_id, qr_path 
        except sqlite3.Error as e:
            logger.error(f"Error adding new user: {e}")
            return None
