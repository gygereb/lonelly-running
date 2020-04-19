import sys, os, os.path, pprint

lonelly_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if lonelly_path not in sys.path:
    sys.path.insert(0, lonelly_path)

import argparse
cli_arg_parser = argparse.ArgumentParser()
cli_arg_parser.add_argument('lick_list', nargs='*')

from strapon import bear_toes


if __name__ == "__main__":

    args = cli_arg_parser.parse_args()

    bear_toes.JumpingBearLeg.main(*args.lick_list)
