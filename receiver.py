#!/usr/bin/env python3

import configparser
import time
import database_connection
import RPi.GPIO as GPIO

from pySX127x.SX127x.LoRa import *
from pySX127x.SX127x.board_config import BOARD


class Receiver(LoRa):
    debug = False

    def __init__(self, verbose=False, debug=False):
        BOARD.setup()
        # sometimes the transreceiver throws strange assertions errors, restart before initialization fixes that
        self.reset()
        super(Receiver, self).__init__(verbose)
        self.debug = debug
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)
        self.setup()

    def on_rx_done(self):
        print("IRQ_RX")
        print("RSSI: " + str(self.get_pkt_rssi_value()) + " dBm; SNR: " + str(self.get_pkt_snr_value()) + " dBm")
        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)
        if self.debug:
            print("Print payload: ")
            print(bytes(payload).decode("utf-8", 'ignore'))
        # check the CrcOnPayload bit in the register and check for CRC errors on the payload
        if self.get_hop_channel().get('crc_on_payload') == 1 and self.get_irq_flags().get('crc_error') == 0:
            print("Packet integrity ok, continuing")
            records = list(filter(None, bytes(payload).decode("utf-8", 'ignore').split(";")))
            db = database_connection.DatabaseConnection()
            machine = records[0]
            saved = False
            for i in range(1, len(records)):
                if self.debug:
                    print(records[i])
                row = records[i].split(",")
                tran_id = row[0]
                motor_name = row[1]
                start_time = row[2]

                if self.debug:
                    print("Saving {} : {} : {} : {} to database".format(motor_name, start_time, tran_id, machine))

                saved = db.save_records(motor_name, start_time, tran_id, machine)
                if not saved:
                    # something happened when saving one of the records, do not send ACK
                    break

            if saved:
                db.close_connection()
                time.sleep(2)
                print("Sending ACK")
                self.write_payload([255, 255, 0, 0, 65, 67, 75, 0])  # Send ACK
                self.set_mode(MODE.TX)
                time.sleep(2)
            print("Switching back to continuous receive mode")
            self.reset_ptr_rx()
            self.set_mode(MODE.RXCONT)

    def on_tx_done(self):
        print("IRQ_TX")
        print(self.get_irq_flags())

    def on_cad_done(self):
        print("IRQ_CadDone ")
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
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)  # Receiver mode
        while True:
            pass

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

    def reset(self):
        print("Resetting board...")
        GPIO.setup(22, GPIO.OUT)
        GPIO.output(22, 0)
        time.sleep(.01)
        GPIO.output(22, 1)
        time.sleep(.01)
        print("Reset done!")
