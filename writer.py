# encoding: utf-8
# Created by Jabok @ Friday July 24th 2015
"""Classes and utilities for writing to ePub files"""
import os
import zipfile
import io
from PIL import Image


def get_local(*path):
    """Returns the given path relative to the location of this script"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.join(*path)))

def template(*path):
    return get_local("templates", *path)    

# Globals
TITLE_FILENAME = "titlepage.xhtml"
CONTENT_FILENAME = "content.opf"
CONTAINER_PATH = "META-INF/container.xml"
MIMETYPE_FILENAME = "mimetype"
TOC_FILENAME = "toc.ncx"

CONTENT_TEMPLATE_FILE = template("content.tpl")
META_TEMPLATE_FILE = template("meta.tpl")
TITLE_TEMPLATE_FILE = template("title.tpl")
TOC_TEMPLATE_FILE = template("toc.tpl")
TOC_NAV_POINT_TEMPLATE_FILE = template("nav_point.tpl")
MANIFEST_ITEM_TEMPLATE_FILE = template("manifest_item.tpl")
SPINE_ITEM_TEMPLATE_FILE = template("spine_item.tpl")

# Other stuff
def get_image_size(imagepath):
    """Returns the size of the given image"""
    img = Image.open(imagepath)
    return img.size


def read_description(file):
    with open(file) as f:
        text = f.read()
    return text


_type_map = {
    "jpg": "jpeg",
    "JPEG": "jpeg",
}
def get_image_type(filename):
    """Returns the media-type of the given image ending"""
    ending = filename.rsplit(".", 1)[-1]
    return "image/" + _type_map.get(ending, ending)


_meta_handlers = {
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


_default_metadata = {
    "language": "en",
    "description": "This item has no designated description ;)",
}

def create_content_page(title, cover_file_name, author, chapters, images, metadata=None):
    """Creates the content.opf file of an epub book
    specs: The specification dictionary of the comic
    spine: A list of the files in the finished epub
    directory: Where to put everything
    """
    if metadata is None: metadata = {}
    
    with open(MANIFEST_ITEM_TEMPLATE_FILE) as f:
        manifest_template = f.read()
    
    with open(SPINE_ITEM_TEMPLATE_FILE) as f:
        spine_template = f.read()
    
    # Add optional meta information :)
    meta_lines = []
    
    combined_metadata = _default_metadata.copy()
    combined_metadata.update(metadata)
    
    for meta_type, value in combined_metadata.items():
        meta_lines += _meta_handlers[meta_type](value)
    
    extrameta = "\n".join(meta_lines)
    
    # Throw together the manifest and spine
    
    manifest_lines = []
    spine_lines = []
    
    def add_manifest(item_id, url, media_type):
        text = manifest_template.format_map({
            "id": item_id,
            "url": url,
            "media_type": media_type,
        })
        manifest_lines.append(text)
    
    def add_spine(item_id):
        text = spine_template.format_map({"id": item_id})
        spine_lines.append(text)
    
    add_manifest("title", TITLE_FILENAME, "application/xhtml+xml")
    add_spine("title")
    
    for (local_id, local_file) in chapters:
        add_manifest(local_id, local_file, "application/xhtml+xml")
        add_spine(local_id)
    
    for (local_id, local_file) in images:
        image_type = get_image_type(local_file)
        add_manifest(local_id, local_file, image_type)
    
    add_manifest("ncx", "toc.ncx", "application/x-dtbncx+xml")
    
    spine = "\n".join(spine_lines)
    manifest = "\n".join(manifest_lines)
    
    split_name = author.rsplit(" ", 1)
    if len(split_name) > 1:
        first_names, last_name = split_name
        authorformat = "{},{}".format(last_name, first_names)
    else:
        authorformat = author
    
    # Format everything :D
    with open(CONTENT_TEMPLATE_FILE) as f:
        content_template = f.read()
    
    content = content_template.format(
        title=title,
        author=author,
        cover=cover_file_name,
        authorformat=authorformat,
        extrameta=extrameta,
        manifest=manifest,
        spine=spine)
    return content


def create_title_page(cover_bytes, cover_file):
    """Creates a html title page based on the given cover image"""
    with open(TITLE_TEMPLATE_FILE) as f:
        template = f.read()
    
    image = Image.open(io.BytesIO(cover_bytes))
    width, height = image.size
    text = template.format_map({
        "width": width, 
        "height": height, 
        "filename": cover_file
    })
    return text


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
    
    
    def add_chapter(self, title, local_file, text):
        """Adds a chapter to the ePub"""
        self.file.writestr(local_file, text)
        self.source.chapters.append((title, local_file))
        print("- Chapter added: {!r}".format(title))
    
    
    def add_image(self, title, local_file, image_bytes):
        """Adds the given image to the ePub"""
        if not isinstance(image_bytes, bytes):
            raise Exception("Image bytes should be 'bytes' not a {}".format(
                type(image_bytes)))
        self.file.writestr(local_file, image_bytes)
        self.source.images.append((title, local_file))
        print("- Image added: {!r}".format(title))
    
    
    def add_cover(self, image_type, image_bytes):
        """Uses the given binary image data as the cover for the ePub"""
        cover_file = "cover.{}".format(image_type.replace(".", ""))
        self.add_image("cover", cover_file, image_bytes)
        self.source.cover_bytes = image_bytes
        self.source.cover_file = cover_file
        print("- Added cover")
    
    
    def compile_title_page(self):
        """Compiles the title page for the ePub"""
        if self.source.cover_bytes:
            title_content = create_title_page(
                self.source.cover_bytes, self.source.cover_file)
            self.file.writestr(TITLE_FILENAME, title_content)
        print("- Compiled title page")
    
    
    def compile_index(self):
        """Compiles the index file for the ePub"""
        content = create_content_page(
            self.source.title, self.source.cover_file, self.source.author, 
            self.source.chapters, self.source.images, self.source.metadata)
        self.file.writestr(CONTENT_FILENAME, content)
        print("- Compiled index file")
    
    
    def compile_table_of_contents(self):
        """Compiles a .ncx table of content for the ePub"""
        with open(TOC_TEMPLATE_FILE) as f:
            toc_template = f.read()
        
        with open(TOC_NAV_POINT_TEMPLATE_FILE) as f:
            nav_point_template = f.read()
        
        nav_points = []
        nav_points.append(nav_point_template.format_map({
            "number": 1,
            "chapter": "Cover",
            "chapter_file": TITLE_FILENAME,
        }))
        for num, (title, filename) in enumerate(self.source.chapters, 2):
            nav_points.append(nav_point_template.format_map({
                "number": num,
                "chapter": title,
                "chapter_file": filename,
            }))
        text = toc_template.format_map({
            "title": self.source.title,
            "nav_points": "\n".join(nav_points),
        })
        self.file.writestr(TOC_FILENAME, text)
        print("- Compiled table of contents")
        
    
    def compile_meta(self):
        """Adds the META-INF pointer file"""
        with open(META_TEMPLATE_FILE) as f:
            meta_template = f.read()
        
        self.file.writestr(CONTAINER_PATH, meta_template)
        self.file.writestr(MIMETYPE_FILENAME, "application/epub+zip")
        print("- Compiled metadata pointer file")
    
    
    def close(self):
        """Compiles the index and meta files and closes the underlying archive"""
        self.compile_title_page()
        self.compile_index()
        self.compile_meta()
        self.compile_table_of_contents()
        self.file.close()