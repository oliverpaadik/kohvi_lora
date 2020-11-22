#!/usr/bin/env python3

import enum
import sys
import argparse

from receiver import Receiver
from transmitter import Transmitter


class Role(enum.Enum):
    transmitter = 1
    receiver = 2


def runner():
    debug = False

    parser = argparse.ArgumentParser()
    parser.add_argument("process", help="select whether the module acts as (t)ransmitter or (r)eceiver")
    parser.add_argument("-d", "--debug", help="turn on extra logging level", action="store_true")
    args = parser.parse_args()

    if args.debug:
        print("Debug turned on")
        debug = True
    if args.process == 't' or args.process == 'T':
        role = Role.transmitter
        print("Module acting as transmitter")
    elif args.process == 'r' or args.process == 'R':
        role = Role.receiver
        print("Module acting as receiver")
    else:
        print("Cannot parse the argument, use either 't' or 'r'")
        sys.exit(-1)

    if role == Role.receiver:
        print("Starting receiver")
        if debug:
            lora = Receiver(verbose=False, debug=True)
        else:
            lora = Receiver(verbose=False, debug=False)

        try:
            if debug:
                print(lora)
            lora.start()
        except KeyboardInterrupt:
            sys.stdout.flush()
            print("Exit")
            sys.stderr.write("KeyboardInterrupt\n")
        finally:
            lora.stop()
            sys.stdout.flush()
            print("Exit")
    elif role == Role.transmitter:
        print("Starting transmitter")
        if debug:
            lora = Transmitter(verbose=False, debug=True)
        else:
            lora = Transmitter(verbose=False, debug=False)

        if debug:
            print(lora)
        lora.start()
        print("Stopping transmitter.")
        lora.stop()


if __name__ == '__main__':
    runner()
