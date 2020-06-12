"""Console script for pydhall."""
import sys
import argparse
from pathlib import Path

from pydhall.parser import Dhall
from pydhall.ast.type_error import DhallTypeError
from pydhall.ast.import_.base import LocalFile


def normalize(args):
    if not args.file:
        src = sys.stdin.read()
        module = Dhall.p_parse(src)
    else:
        with open(src) as f:
            src = f.read()
    try:
        module.type()
    except DhallTypeError as e:
        raise
        sys.stderr.write("Error: ")
        sys.stderr.write(str(e))
        sys.stderr.write("\n")
        sys.exit(1)
    print(module.eval().quote(normalize=True).dhall())


def hash(args):
    if not args.file:
        src = sys.stdin.read()
        module = Dhall.p_parse(src)
        origin = LocalFile(Path(os.getcwd()).joinpath("<stdin>"), None, 0)
    else:
        with open(args.file) as f:
            src = f.read()
        origin = LocalFile(Path(args.file), None, 0)
    module = Dhall.p_parse(src)
    module = module.resolve(origin)
    try:
        module.type()
    except DhallTypeError as e:
        raise
        sys.stderr.write("Error: ")
        sys.stderr.write(str(e))
        sys.stderr.write("\n")
        sys.exit(1)
    print(module.eval().quote(normalize=True).sha256())


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    p_normalize = subparsers.add_parser('normalize')
    p_normalize.set_defaults(func=normalize)

    p_hash = subparsers.add_parser('hash')
    p_hash.add_argument(
        "--file",
        help="Read expression from a file instead of standard input",
        default='')
    p_hash.set_defaults(func=hash)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
