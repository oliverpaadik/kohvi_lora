#!/usr/bin/env python3

import configparser
import time
import socket
import database_connection

from pySX127x.SX127x.LoRa import *
from pySX127x.SX127x.board_config import BOARD


class Transmitter(LoRa):
    debug = False

    def __init__(self, verbose=False, debug=False):
        BOARD.setup()
        super(Transmitter, self).__init__(verbose)
        self.debug = debug
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)
        self.ack_received = False
        self.setup()

    def on_rx_done(self):
        print("IRQ_RX")
        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)
        message = bytes(payload).decode("utf-8", 'ignore')
        message = message[2:-1]
        if message == "ACK":
            self.ack_received = True

    def on_tx_done(self):
        print("IRQ_TX")
        print(self.get_irq_flags())

    def on_cad_done(self):
        print("IRQ_CadDone")
        print(self.get_irq_flags())

    def on_rx_timeout(self):
        print("IRQ_RXTimeout")
        print(self.get_irq_flags())

    def on_valid_header(self):
        print("IRQ_ValidHeader")
        print(self.get_irq_flags())

    def on_payload_crc_error(self):
        print("IRQ_PayloadCrcError")
        print(self.get_irq_flags())

    def start(self):
        db = database_connection.DatabaseConnection()
        records = db.get_records()
        if records:
            csv_string = socket.gethostname() + ";"
            for row in records:
                # append id to csv string
                csv_string += str(row[0])
                csv_string += ","
                # append drink name to csv string
                csv_string += str(row[1])
                csv_string += ","
                # append date to csv string, end with ';'
                csv_string += str(row[2])
                csv_string += ";"

            # print("Generated CSV string: " + csv_string)
            # print(list(bytes(csv_string, encoding="utf-8")))
            self.write_payload(list(bytes(csv_string.strip(), encoding="utf-8")))
            self.set_mode(MODE.TX)
            print("Sent {} records".format(len(records)))
            time.sleep(1)
            self.set_mode(MODE.RXCONT)

            start = time.time()
            # wait for 10 seconds or when the ACK is received
            while (time.time() - start <= 10) and not self.ack_received:
                pass
            if not self.ack_received:
                print("Didn't receive ACK, assuming something happened when transmitting data.")
            else:
                print("ACK received. Marking records as sent and exiting.")
                db.close_records()
        else:
            print("No records to send")

    def setup(self):
        # use the config.ini for configuration
        config = configparser.ConfigParser()
        config.read('config.ini')

        self.set_pa_config(pa_select=1, max_power=21, output_power=15)
        self.set_freq(float(config['GENERAL']['Frequency']))
        self.set_bw(int(config['GENERAL']['Bandwidth']))
        self.set_coding_rate(int(config['GENERAL']['CodingRate']))
        self.set_spreading_factor(int(config['GENERAL']['SpreadingFactor']))
        self.set_rx_crc(True)
        assert (self.get_agc_auto_on() == 1)

    def stop(self):
        self.set_mode(MODE.SLEEP)
        BOARD.teardown()
