from paths import * 
import sqlite3
import logging
# Configure the logger
logging.basicConfig(level=logging.INFO, filename='logs\\user.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class User:
    """
    A class representing a user of the parking system.

    Attributes:
        user_id (int): The ID of the user.
        users_db (sqlite3.Connection): Connection to the users database.
        cursor_users (sqlite3.Cursor): Cursor for executing SQL queries on the users database.
        parking_tickets_db (sqlite3.Connection): Connection to the parking tickets database.
        cursor_parking_ticket (sqlite3.Cursor): Cursor for executing SQL queries on the parking tickets database.
    """
    def __init__(self, user_id, users_db_name=users_db_path, parking_tickets=parking_tickets_path):
        """
        Initializes the User class.

        Args:
            user_id (int): The ID of the user.
            users_db_name (str): The name of the users database file.
        """
        try:
            self.user_id = user_id
            self.users_db = sqlite3.connect(users_db_name)
            self.cursor_users = self.users_db.cursor()
            self.parking_tickets_db = sqlite3.connect(parking_tickets)
            self.cursor_parking_ticket = self.parking_tickets_db.cursor()
            logger.info(f"User {user_id} connected to databases")
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")

    def __del__(self):
        """
        Closes all database connections when the object is deleted.
        """
        try:
            self.users_db.close()
            self.parking_tickets_db.close()
            logger.info("User databases closed")
        except sqlite3.Error as e:
            logger.error(f"Error closing database connection: {e}")

    def get_balance(self):
        """
        Retrieves the balance of the user.

        Returns:
            float: The balance of the user.
        """
        try:
            get_query = f"SELECT amount FROM user_data WHERE user_id = {self.user_id};"
            self.cursor_users.execute(get_query)
            balance = self.cursor_users.fetchone()[0]
            logger.info(f"Retrieved balance for user {self.user_id}")
            return balance
        except sqlite3.Error as e:
            logger.error(f"Error retrieving balance: {e}")
            return 0.0

    def get_all_history(self):
        """
        Retrieves the parking history of the user.

        Returns:
            list: A list of tuples containing parking ticket information for the user.
        """
        try:
            get_query = f"SELECT * FROM parking_tickets WHERE user_id = {self.user_id}"
            self.cursor_parking_ticket.execute(get_query)
            history = self.cursor_parking_ticket.fetchall()
            logger.info(f"Retrieved parking history for user {self.user_id}")
            return history
        except sqlite3.Error as e:
            logger.error(f"Error retrieving parking history: {e}")
            return []

    def add_balance(self, amount):
        """
        Adds balance to the user's account.

        Args:
            amount (float): The amount to be added to the user's balance.
        """
        try:
            self.cursor_users.execute(f"SELECT amount FROM user_data WHERE user_id = {self.user_id};")
            current_amount = self.cursor_users.fetchone()[0]
            final_balance = current_amount + amount
            update_query = f"UPDATE user_data SET amount = {final_balance} WHERE user_id = {self.user_id};"
            self.cursor_users.execute(update_query)
            self.users_db.commit()
            logger.info(f"Added balance {amount} to user {self.user_id}. New balance is {final_balance}")
        except sqlite3.Error as e:
            logger.error(f"Error adding balance: {e}")

