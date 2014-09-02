import sys

from .args import parser

def main():
    args = parser.parse_args(sys.argv[1:])

    try:
        args.func
    except AttributeError:
        parser.print_help()
        exit(1)

    if args.cubes_debug:
        args.func(args)
    else:
        try:
            args.func(args)
        except CubesError as e:
            sys.stderr.write("ERROR: %s\n" % e)
            exit(1)
        except MissingPackageError as e:
            sys.stderr.write("MISSING PACKAGE ERROR: %s\n" % e)
            exit(2)