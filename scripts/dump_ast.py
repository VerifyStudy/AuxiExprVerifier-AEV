#!/usr/bin/python3

import argparse
from pycparser import parse_file

if __name__ == "__main__":
    argparser = argparse.ArgumentParser('Dump AST')
    argparser.add_argument('filename', help='name of file to parse')
    argparser.add_argument('--coord', help='show coordinates in the dump',
                           action='store_true')
    args = argparser.parse_args()

    ast = parse_file(args.filename, use_cpp=False)
    ast.show(showcoord=args.coord)
