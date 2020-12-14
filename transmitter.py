#!/usr/bin/env python3

import configparser
import time
import socket
import database_connection
import RPi.GPIO as GPIO
import logging
from pySX127x.SX127x.LoRa import *
from pySX127x.SX127x.board_config import BOARD


class Transmitter(LoRa):

    def __init__(self, verbose=False):
        BOARD.setup()
        # sometimes the transreceiver throws strange assertions errors, restart before initialization fixes that
        self.reset()
        super(Transmitter, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)
        self.ack_received = False
        self.setup()

    def on_rx_done(self):
        logging.debug("IRQ_RX")
        logging.info("RSSI: " + str(self.get_pkt_rssi_value()) + " dBm; SNR: " + str(self.get_pkt_snr_value()) + " dBm")
        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)
        message = bytes(payload).decode("utf-8", 'ignore')
        if message == "ACK":
            self.ack_received = True

    def on_tx_done(self):
        logging.debug("IRQ_TX")

    def on_cad_done(self):
        logging.debug("IRQ_CadDone")

    def on_rx_timeout(self):
        logging.warning("IRQ_RXTimeout")

    def on_valid_header(self):
        logging.debug("IRQ_ValidHeader")

    def on_payload_crc_error(self):
        logging.error("IRQ_PayloadCrcError")

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
            logging.info("Sent {} records".format(len(records)))
            time.sleep(1)
            self.set_mode(MODE.RXCONT)

            start = time.time()
            # wait for 10 seconds or when the ACK is received
            while (time.time() - start <= 15) and not self.ack_received:
                pass
            if not self.ack_received:
                logging.warning("Didn't receive ACK, assuming something happened when transmitting data.")
            else:
                logging.info("ACK received. Marking records as sent and exiting.")
                db.close_records()
        else:
            logging.debug("No records to send")

    def setup(self):
        # use the parameters.ini for configuration
        config = configparser.ConfigParser()
        #config.read('parameters.ini')
        config.read("/share/parameters.ini")

        self.set_pa_config(pa_select=1, max_power=19, output_power=13)
        self.set_freq(float(config['GENERAL']['Frequency']))
        self.set_bw(int(config['GENERAL']['Bandwidth']))
        self.set_coding_rate(int(config['GENERAL']['CodingRate']))
        self.set_spreading_factor(int(config['GENERAL']['SpreadingFactor']))
        self.set_rx_crc(True)
        assert (self.get_agc_auto_on() == 1)

    def stop(self):
        self.set_mode(MODE.SLEEP)
        BOARD.teardown()

    def reset(self):
        logging.debug("Resetting board...")
        GPIO.setup(22, GPIO.OUT)
        GPIO.output(22, 0)
        time.sleep(.01)
        GPIO.output(22, 1)
        time.sleep(.01)
        logging.debug("Reset done!")
