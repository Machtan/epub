# coding: utf-8
# Created by Jabok @ July 28th 2014
# create_epub.py
"""Command-line utility for the ePub compilation library"""
import os
import sys
import friendlytoml as toml
from argparse import ArgumentParser
from compile import compile_epub_from_specification

def main(args=sys.argv[1:]):
    """Entry point"""
    description = "Compiles an ePub from a markdown source and a TOML specification"
    parser = ArgumentParser(description=description)

    parser.add_argument(
        "spec_file",
        help="The spec of the book!")
    parser.add_argument(
        "-t", "--target_path", default=None,
        help="A specific path to compile the ePub to")
    parser.add_argument(
        "-a", "--assume_html", default=False,
        help="Don't try to compile any of the text source files")
    parser.add_argument(
        "-r", "--raw_spec", default=False,
        help="Interpret the spec_file argument as the contents of the\
        specification file, instead of the path to it")

    parsed = parser.parse_args(args)
    spec_file = parsed.spec_file
    if not parsed.raw_spec:
        if not os.path.exists(spec_file):
            return print("Spec does not exist: '{}'".format(spec_file))
        spec = toml.load(spec_file)
    else:
        spec = toml.loads(spec_file)

    directory = os.path.dirname(os.path.abspath(spec_file))

    compile_epub_from_specification(
        spec, directory, target_path=parsed.target_path,
        source_is_html=parsed.assume_html)


if __name__ == '__main__':
    main()
