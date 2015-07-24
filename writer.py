# encoding: utf-8
# Created by Jabok @ Friday July 24th 2015
"""Classes and utilities for writing to ePub files"""
import os
import zipfile
import io
from PIL import Image


# Globals
TITLE_FILENAME = "titlepage.html"
CONTENT_FILENAME = "content.opf"
CONTAINER_PATH = "META-INF/container.xml"
MIMETYPE_FILENAME = "mimetype"
TOC_FILENAME = "toc.ncx"

CONTENT_TEMPLATE_FILE = "content.tpl"
META_TEMPLATE_FILE = "meta.tpl"
TITLE_TEMPLATE_FILE = "title.tpl"
TOC_TEMPLATE_FILE = "toc.tpl"
TOC_NAV_POINT_TEMPLATE_FILE = "nav_point.tpl"
MANIFEST_ITEM_TEMPLATE_FILE = "manifest_item.tpl"
SPINE_ITEM_TEMPLATE_FILE = "spine_item.tpl"

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
    manifest_template = quick_load(MANIFEST_ITEM_TEMPLATE_FILE)
    spine_template = quick_load(SPINE_ITEM_TEMPLATE_FILE)
    
    # Add optional meta information :)
    meta_lines = []
    for item, handler in _meta_map.items():
        if item in metadata:
            meta_lines += handler(metadata[item])
    extrameta = "\n".join(meta_lines)
    
    # Throw together the manifest and spine
    
    manifest_lines = []
    
    covertype = cover_file_name.split(".")[-1]
    cover_text = manifest_template.format_map({
        "url": cover_file_name, 
        "id": "cover", 
        "media_type": "image/"+covertype
    })
    manifest_lines.append(cover)
    
    spine_lines = []
    first_names, last_name = author.rsplit(" ", 1)
    authorformat = last_name + "," + first_names
    for num, chapter in enumerate(spine):
        chapter = manifest_template.format_map({
            "url": item, 
            "id": num, 
            "media_type": "application/xhtml+xml"
        })
        manifest_lines.append(chapter)
        spine_lines.append(spine_template.format(num))
    
    toc_text = manifest_template.format_map({
        "url": "toc.ncx", 
        "id": "ncx", 
        "media_type": "application/x-dtbncx+xml"
    })
    
    spine_text = "\n".join(spine_lines)
    manifest = "\n".join(manifest_lines)
    
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
    image = Image.open(io.BytesIO(cover_bytes))
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
        self.source.index.append(title)
        print("- Chapter added: {!r}".format(title))
    
    
    def add_image(self, image_name, image_bytes):
        """Adds the given image to the ePub"""
        if not isinstance(image_bytes, bytes):
            raise Exception("Image bytes should be 'bytes' not a {}".format(
                type(image_bytes)))
        self.file.writestr(image_name, image_bytes)
        print("- Image added: {!r}".format(image_name))
    
    
    def add_cover(self, image_type, image_bytes):
        """Uses the given binary image data as the cover for the ePub"""
        image_type = image_type.replace(".", "")  # Ensure proper endings (/bad memory)
        cover_name = "cover.{}".format(image_type)
        self.add_image(cover_name, image_bytes)
        self.source.cover_bytes = image_bytes
        self.source.cover_name = cover_name
        print("- Added cover")
    
    
    def compile_title_page(self):
        """Compiles the title page for the ePub"""
        if self.source.cover_bytes:
            title_content = create_title_page(
                self.source.cover_name, self.source.cover_bytes)
            self.file.writestr(TITLE_FILENAME, title_content)
            if (not self.source.index) or self.source.index[0] != TITLE_FILENAME:
                self.source.index.insert(0, TITLE_FILENAME)
        print("- Compiled title page")
    
    
    def compile_index(self):
        """Compiles the index file for the ePub"""
        content = create_content_page(
            self.source.title, self.source.cover_name, self.source.author, 
            self.source.index, self.source.metadata)
        self.file.writestr(CONTENT_FILENAME, content)
        print("- Compiled index file")
    
    
    def compile_toc(self):
        """Compiles a .ncx table of content for the ePub"""
        toc_template = quick_load(TOC_TEMPLATE_FILE)
        nav_point_template = quick_load(TOC_NAV_POINT_TEMPLATE_FILE)
        nav_points = []
        for num, chapter in enumerate(self.source.index[1:], 1):
            nav_points.append(nav_point_template.format_map({
                "number": num,
                "chapter": chapter.rsplit(".", 1)[0],
                "chapter_file": chapter,
            }))
        text = toc_template.format_map({
            "title": self.source.title,
            "nav_points": "\n".join(nav_points),
        })
        self.file.writestr(TOC_FILENAME, text)
        print("- Compiled table of contents")
        
    
    def compile_meta(self):
        """Adds the META-INF pointer file"""
        self.file.writestr(CONTAINER_PATH, quick_load(META_TEMPLATE_FILE))
        self.file.writestr(MIMETYPE_FILENAME, "application/epub+zip")
        print("- Compiled metadata pointer file")
    
    
    def close(self):
        """Compiles the index and meta files and closes the underlying archive"""
        self.compile_title_page()
        self.compile_index()
        self.compile_meta()
        self.compile_toc()
        self.file.close()