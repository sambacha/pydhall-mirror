"""Console script for pydhall."""
import sys
import argparse
from pydhall.parser import Dhall
from pydhall.ast.type_error import DhallTypeError


def normalize(args):
    src = sys.stdin.read()
    module = Dhall.p_parse(src)
    try:
        module.type()
    except DhallTypeError as e:
        sys.stderr.write("Error: ")
        sys.stderr.write(str(e))
        sys.stderr.write("\n")
        sys.exit(1)
    print(module.eval())


def hash(args):
    src = sys.stdin.read()
    module = Dhall.p_parse(src)
    try:
        module.type()
    except DhallTypeError as e:
        sys.stderr.write("Error: ")
        sys.stderr.write(str(e))
        sys.stderr.write("\n")
        sys.exit(1)
    print(module.sha256())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    p_normalize = subparsers.add_parser('normalize')
    p_normalize.set_defaults(func=normalize)

    p_hash = subparsers.add_parser('hash')
    p_hash.set_defaults(func=hash)

    args = parser.parse_args()
    args.func(args)
