import mysql.connector as mariadb
from mysql.connector import Error
import datetime


class DatabaseConnection:

    def __init__(self):
        self.connection = mariadb.connect(user='root', password='root', database='coffee')
        self.cursor = self.connection.cursor()
        self.records = None
        print("Connecting to database... OK")

    # retrieve 6 first (because of the payload size limit) records where transmit is null
    def get_records(self):
        if not self.records:
            try:
                self.cursor.execute(
                    "SELECT tran_id, motor_name, start_time, id FROM motor_log WHERE transmit IS NULL "
                    "ORDER BY id ASC LIMIT 6")

                self.records = self.cursor.fetchall()
                return self.records
            except Error as error:
                print("Error while fetching from database: {}".format(error))
                if self.connection.is_connected():
                    self.cursor.close()
                    self.connection.close()
                    print("Connection to database closed.")

        else:
            return self.records

    # mark records which were sent as transmitted (transmit = timestamp)
    def close_records(self):
        try:
            if not self.connection:
                self.__init__()
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for row in self.records:
                self.cursor.execute(
                    "UPDATE motor_log SET transmit=%s WHERE id=%s", (current_time, row[3]))
            self.connection.commit()
        except Error as error:
            print("Error while committing to database: {}. Rollback commenced".format(error))
            self.connection.rollback()

        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("Connection to database closed.")

    # insert records parsed from the payload to the table
    def save_records(self, motor_name, start_time, tran_id, machine):
        try:
            if not self.connection:
                self.__init__()
            self.cursor.execute(
                "INSERT motor_log (motor_name, start_time, tran_id, machine) VALUES (%s, %s, %s, %s)",
                (motor_name, start_time, tran_id, machine))

            self.connection.commit()
            return True

        except Error as error:
            print("Error while commiting to database: {}. \nRollback commenced".format(error))
            self.connection.rollback()
            return False

    # close connection to db
    def close_connection(self):
        if self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            print("Connection to database closed.")
