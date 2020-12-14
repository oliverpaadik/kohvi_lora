#!/usr/bin/env python3

import configparser
import time
import database_connection
import RPi.GPIO as GPIO
import logging

from pySX127x.SX127x.LoRa import *
from pySX127x.SX127x.board_config import BOARD


class Receiver(LoRa):

    def __init__(self, verbose=False):
        BOARD.setup()
        # sometimes the transreceiver throws strange assertions errors, restart before initialization fixes that
        self.reset()
        super(Receiver, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)
        self.setup()

    def on_rx_done(self):
        logging.debug("IRQ_RX")
        logging.info("RSSI: " + str(self.get_pkt_rssi_value()) + " dBm; SNR: " + str(self.get_pkt_snr_value()) + " dBm")
        self.clear_irq_flags(RxDone=1)

        # check the CrcOnPayload bit in the register and check for CRC errors on the payload
        if self.get_hop_channel().get('crc_on_payload') == 1 and self.get_irq_flags().get('crc_error') == 0:
            logging.debug("Packet integrity ok, continuing")
            payload = self.read_payload(nocheck=True)
            logging.info("Payload: {}".format(bytes(payload).decode("utf-8", 'ignore')))
            records = list(filter(None, bytes(payload).decode("utf-8", 'ignore').split(";")))
            record_count = len(records)-1
            db = database_connection.DatabaseConnection()
            machine = records[0]
            saved = False
            for i in range(1, record_count):
                row = records[i].split(",")
                id_external = row[0]
                motor_name = row[1]
                start_time = row[2]

                # logging.debug("Saving {} : {} : {} : {} to database".format(motor_name, start_time, tran_id, machine))

                saved = db.save_records(motor_name, start_time, id_external, machine)
                if not saved:
                    # something happened when saving one of the records, do not send ACK
                    logging.warning("Could not save records, not sending ACK")
                    break

            if saved:
                db.close_connection()
                time.sleep(2)
                logging.info("Saved {} records".format(record_count))
                logging.debug("Sending ACK")
                self.write_payload([65, 67, 75])  # Send ACK
                self.set_mode(MODE.TX)
                time.sleep(2)
            logging.debug("Switching back to continuous receive mode")
            self.reset_ptr_rx()
            self.set_mode(MODE.RXCONT)

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
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)  # Receiver mode
        while True:
            pass

    def setup(self):
        # use the parameters.ini for configuration
        config = configparser.ConfigParser()
        config.read('parameters.ini')

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
