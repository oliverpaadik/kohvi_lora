#!/usr/bin/env python3

import enum
import sys
import argparse
import logging
from receiver import Receiver
from transmitter import Transmitter


class Role(enum.Enum):
    transmitter = 1
    receiver = 2


def runner():

    parser = argparse.ArgumentParser()
    parser.add_argument("process", help="select whether the module acts as (t)ransmitter or (r)eceiver")
    parser.add_argument("-d", "--debug", help="turn on extra logging level", action="store_true")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(stream=sys.stdout, filemode="a",
                            format="%(asctime)s - %(module)-12s - %(levelname)-8s - %(message)s",
                            datefmt="%d-%m-%Y %H:%M:%S",
                            level=logging.DEBUG)
        logging.debug("Logging level set to DEBUG")
    else:
        # filename="/share/log.txt"
        logging.basicConfig(stream=sys.stdout, filemode="a",
                            format="%(asctime)s - %(module)-12s - %(levelname)-8s - %(message)s",
                            datefmt="%d-%m-%Y %H:%M:%S",
                            level=logging.INFO)

    if args.process == 't' or args.process == 'T':
        role = Role.transmitter
        logging.debug("Module acting as transmitter")
    elif args.process == 'r' or args.process == 'R':
        role = Role.receiver
        logging.debug("Module acting as receiver")
    else:
        print("Cannot parse the argument, use either 't/T' or 'r/R'")
        sys.exit(-1)

    if role == Role.receiver:
        lora = Receiver(verbose=False)

        try:
            print(lora)
            lora.start()
        except KeyboardInterrupt:
            sys.stdout.flush()
            sys.stderr.write("KeyboardInterrupt\n")
        finally:
            lora.stop()
            sys.stdout.flush()
            logging.debug("Exiting the program")

    elif role == Role.transmitter:
        lora = Transmitter(verbose=False)
        print(lora)
        lora.start()
        logging.debug("Stopping transmitter.")
        lora.stop()


if __name__ == '__main__':
    runner()
