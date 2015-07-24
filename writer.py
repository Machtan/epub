# encoding: utf-8
# Created by Jabok @ Friday July 24th 2015
"""Classes and utilities for writing to ePub files"""
import os
import zipfile
from PIL import Image


# Globals
TITLE_FILENAME = "titlepage.html"
CONTENT_FILENAME = "content.opf"
CONTAINER_PATH = "META-INF/container.xml"

CONTENT_TEMPLATE_FILE = "content.tpl"
META_TEMPLATE_FILE = "meta.tpl"
TITLE_TEMPLATE_FILE = "title.tpl"

# Other stuff
def get_image_size(imagepath):
    """Returns the size of the given image"""
    img = Image.open(imagepath)
    return img.size


def get_local(*path):
    """Returns the given path relative to the location of this script"""
    return os.path.join(os.path.dirname(__file__), os.path.join(*path))


def quick_load(*path):
    """Loads the text of a local file and closes it again"""
    fpath = get_local(*path)
    with open(fpath) as f:
        text = f.read()
    return text


def read_description(file):
    with open(file) as f:
        text = f.read()
    return text


_meta_map = {
    "series": lambda x: [
        "<meta name='calibre:series' content='{}'/>".format(x),
        "\n<dc:subject>Series</dc:subject>"],
    "volume": lambda x: [
        "<meta name='calibre:series_index' content='{}'/>".format(x)],
    "language": lambda x: [
        "<dc:language>{}</dc:language>".format(x)],
    "description": lambda x: [
        "<dc:description>{}</dc:description>".format(x)],
    "description_file": lambda x: [
        "<dc:description>{}</dc:description>".format(read_description(x))],
    "tags": lambda tags: [
        "<dc:subject>{}</dc:subject>".format(tag) for tag in tags]
}
def create_content_page(title, cover_file_name, author, spine, metadata={}):
    """Creates the content.opf file of an epub book
    specs: The specification dictionary of the comic
    spine: A list of the files in the finished epub
    directory: Where to put everything
    """
    manifest_template = """<item href='{0}' id='{1}' media-type='{2}'/>"""
    spine_template = """<itemref idref='{0}'/>"""
    
    # Add optional meta information :)
    meta_lines = []
    for item, handler in _meta_map.items():
        if item in metadata:
            meta_lines += handler(metadata[item])
    extrameta = "\n".join(meta_lines)
    
    # Throw together the manifest and spine
    covertype = cover_file_name.split(".")[-1]
    manifest = manifest_template.format(cover_file_name, "cover", "image/"+covertype)
    spine_lines = []
    splat = author.split(" ")
    authorformat = splat[-1]+","+" ".join(splat[:-1])
    for num, item in enumerate(spine):
        manifest += "\n" + manifest_template.format(item, num, "text/html")
        spine_lines.append(spine_template.format(num))
    spine_text = "\n".join(spine_lines)
    
    # Format everything :D
    content_template = quick_load(CONTENT_TEMPLATE_FILE)
    content = content_template.format(
        title=title,
        author=author,
        cover=cover_file_name,
        authorformat=authorformat,
        extrameta=extrameta,
        manifest=manifest,
        spine=spine_text)
    return content


def create_title_page(cover_name, cover_bytes):
    """Creates a html title page based on the given cover image"""
    template = quick_load(TITLE_TEMPLATE_FILE)
    image = PIL.Image.from_bytes(image_bytes)
    w, h = image.size
    return template.format(w, h, cover_name)


class EpubWriter:
    """An ePub archive open for writing"""
    def __init__(self, epub):
        self.source = epub  # The ePub data that this class opens and modifies
        mode = "a" if os.path.exists(epub.path) else "w"
        try:  # Deflate if possible
            self.file = zipfile.ZipFile(
                epub.path, mode=mode, 
                compression=zipfile.ZIP_DEFLATED)
        except Exception:
            self.file = zipfile.ZipFile(
                epub.path, mode=mode, 
                compression=zipfile.ZIP_STORED)
    
    def add_chapter(self, title, text):
        """Adds a chapter to the ePub"""
        self.file.writestr(title, text)
        self.source.index.append(chapter_name)
        print("--- Added {!r}".format(chapter_name))
    
    def add_image(self, image_name, image_bytes):
        """Adds the given image to the ePub"""
        if not isinstance(image_bytes, bytes):
            raise Exception("Image bytes should be 'bytes' not a {}".format(
                type(image_bytes)))
        self.file.writestr(image_name, image_bytes)
    
    def add_cover(self, image_type, image_bytes):
        """Uses the given binary image data as the cover for the ePub"""
        base_cover = os.path.basename(cover_path)
        image_type = image_type.replace(".", "")  # Ensure proper endings (/bad memory)
        cover_name = "cover.{}".format(image_type)
        self.add_image(cover_name, image_bytes)
        self.source.cover_bytes = image_bytes
        self.source.cover_name = cover_name
        print("- Added cover")
    
    def compile_title_page(self, cover_path, spine, zfile):
        """Compiles the title page for the ePub"""
        if self.source.cover_bytes:
            title_content = create_title_page(self.source.cover_name, self.source.cover_bytes)
            zfile.writestr(TITLE_FILENAME, title_content)
            if self.source.index[0] != TITLE_FILENAME:
                self.source.index.insert(0, TITLE_FILENAME)
        print("- Compiled title page")
    
    def compile_index(self):
        """Compiles the index file for the ePub"""
        content = create_content_file(
            self.source.title, self.source.cover_file_name, self.source.author, 
            self.source.index, self.source.metadata)
        self.file.writestr(CONTENT_FILENAME, content)
        print("- Compiled index file")
    
    def compile_meta(self):
        """Adds the META-INF pointer file"""
        self.file.writestr(CONTAINER_PATH, quick_load(META_TEMPLATE_FILE))
        print("- Compiled metadata pointer file")
    
    def close(self):
        """Compiles the index and meta files and closes the underlying archive"""
        self.compile_title_page()
        self.compile_index()
        self.compile_meta()
        self.file.close()