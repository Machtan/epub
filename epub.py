# encoding: utf-8
# Created by Jabok @ Friday July 24th 2015
"""The main ePub class"""
from writer import EpubWriter
from decorators import not_implemented


class Epub:
    """An EPub file"""
    def __init__(
            self, title, author, path, cover_type=None, cover_bytes=bytes(), 
            index=[], images=set(), metadata={}):
        """Creates a new ePub with the given parameters. Use 'load' for existing files."""
        self.path = path
        self.title = title
        self.author = author
        self.index = index
        self.images = images
        self.cover_bytes = cover_bytes
        self.metadata = metadata
        if cover_type:
            self.cover_name = "cover.{}".format(cover_type.replace(".", ""))
        else:
            self.cover_name = "ERROR: DEFAULT COVER NAME NOT CHANGED"
    
    @not_implemented
    def load(self, path):
        """Loads an ePub from the file at the given path"""

    def __enter__(self):
        self.writer = EpubWriter(self)
        return self.writer
    
    def __exit__(self, *args):
        self.writer.close()
    
    @not_implemented
    def get_chapter(self, title):
        """Prints the text of the given chapter"""
    
    @not_implemented
    def print_text(self):
        """Prints the text contents of the ePub"""