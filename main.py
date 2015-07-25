# coding: utf-8
# Created by Jabok @ July 28th 2014
# create_epub.py
"""Command-line utility for the ePub compilation library"""
import os
import sys
import friendlytoml as toml
from argparse import ArgumentParser
from compile import compile_epub_from_specification
from comic import compile_epub_from_folder

def create(spec_file, raw_spec, target_path):
    """The create function"""
    if not raw_spec:
        if not os.path.exists(spec_file):
            return print("Spec does not exist: '{}'".format(spec_file))
        spec = toml.load(spec_file)
    else:
        spec = toml.loads(spec_file)

    directory = os.path.dirname(os.path.abspath(spec_file))

    compile_epub_from_specification(spec, directory, target_path=target_path)


def from_folder(folder, title, author, target_path):
    """The function to create an ePub from a folder"""
    compile_epub_from_folder(
        folder, title=title, author=author, path=target_path)


def main(args=sys.argv[1:]):
    """Entry point"""
    description = "Utility for working with ePub E-Book files"
    parser = ArgumentParser(description=description)
    subparsers = parser.add_subparsers(title="commands")
    
    # ==== EPUB CREATE ====
    create_desc = """Compiles an ePub from a markdown source and a TOML 
    specification. The files in the specification are sought relatively to 
    the location of the specification file, so use absolute paths when 
    needed. If no arguments are given, the created file will be found in 
    the active working directory."""
    create_parser = subparsers.add_parser("create", description=create_desc)
    create_parser.set_defaults(func=create)
    create_parser.add_argument(
        "spec_file",
        help="The spec of the book!")
    create_parser.add_argument(
        "-p", "--target_path", default=None,
        help="""A specific path to compile the ePub to. Defaults to a 
        name/author coupling in the current working directory""")
    create_parser.add_argument(
        "-r", "--raw_spec", default=False,
        help="""Interpret the spec_file argument as the contents of the
        specification file, instead of the path to it""")

    # ==== EPUB FROM_FOLDER ====
    comic_desc = """Creates an ePub file from the images in the given 
    folder"""
    comic_parser = subparsers.add_parser("from_folder", description=comic_desc)
    comic_parser.set_defaults(func=from_folder)
    comic_parser.add_argument("folder")
    comic_parser.add_argument(
        "-t", "--title", default=None,
        help="""The title of the created book (defaults to the folder)""")
    comic_parser.add_argument(
        "-a", "--author", default=None,
        help="""The author of the created book (defaults to the user)""")
    comic_parser.add_argument(
        "-p", "--target_path", default=None,
        help="""Where to put the created file (defaults to a title/author
        combination in the current working directory)""")
    
    # Parse and run
    parsed = parser.parse_args(args)
    if not hasattr(parsed, "func"):
        parser.print_usage()
    else:
        func = parsed.func
        del(parsed.func)
        func(**vars(parsed))

if __name__ == '__main__':
    main()
