from paths import *
import sqlite3
import logging
from datetime import datetime
# Configure the logger
logging.basicConfig(level=logging.INFO, filename='logs\\slots.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
import sqlite3

class Slots:
    """
    A class to manage parking slots.

    Attributes:
        conn (sqlite3.Connection): Connection to the database.
        cursor (sqlite3.Cursor): Cursor for executing SQL queries.
    """
    def __init__(self, db_name=parking_slots_path):
        """
        Initializes the Slots class.

        Args:
            db_name (str): The name of the SQLite database file.
        """
        try:
            self.conn = sqlite3.connect(db_name)
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to the database {db_name}")
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")

    def return_all_available_slots(self):
        """
        Retrieves all available parking slots.

        Returns:
            list: A list of available slot numbers.
        """
        try:
            self.cursor.execute('SELECT slot_number FROM parking_slots WHERE status="free"')
            slots = self.cursor.fetchall()
            logger.info("Retrieved available slots")
            return slots
        except sqlite3.Error as e:
            logger.error(f"Error retrieving available slots: {e}")
            return []

    def book_slot(self, slot_number):
        """
        Books a parking slot.

        Args:
            slot_number (int): The number of the slot to be booked.

        Raises:
            ValueError: If the slot is already occupied or doesn't exist.
        """
        try:
            self.cursor.execute('''
                UPDATE parking_slots 
                SET status="occupied" 
                WHERE slot_number=? AND status="free"
            ''', (slot_number,))
            if self.cursor.rowcount == 0:
                raise ValueError("Slot is already occupied or doesn't exist.")
            else:
                self.conn.commit()
                logger.info(f"Slot {slot_number} booked successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error booking slot: {e}")

    def release_slot(self, slot_number):
        """
        Releases a parking slot.

        Args:
            slot_number (int): The number of the slot to be released.

        Raises:
            ValueError: If the slot is already free or doesn't exist.
        """
        try:
            self.cursor.execute('''
                UPDATE parking_slots 
                SET status="free" 
                WHERE slot_number=? AND status="occupied"
            ''', (slot_number,))
            if self.cursor.rowcount == 0:
                raise ValueError("Slot is already free or doesn't exist.")
            else:
                self.conn.commit()
                logger.info(f"Slot {slot_number} released successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error releasing slot: {e}")

    def return_all_occupied_slots(self):
        """
        Retrieves all occupied parking slots.

        Returns:
            list: A list of occupied slot numbers.
        """
        try:
            self.cursor.execute('SELECT slot_number FROM parking_slots WHERE status="occupied"')
            slots = self.cursor.fetchall()
            logger.info("Retrieved occupied slots")
            return slots
        except sqlite3.Error as e:
            logger.error(f"Error retrieving occupied slots: {e}")
            return []

    def close_connection(self):
        """
        Closes the database connection.
        """
        try:
            self.conn.close()
            logger.info("Database connection closed")
        except sqlite3.Error as e:
            logger.error(f"Error closing database connection: {e}")
