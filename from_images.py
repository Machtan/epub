# encoding: utf-8
# Created by Jabok @ Thursday July 24th 2015
import os
import sys
import argparse
import tempfile
from PIL import Image

from compile import compile_epub
import friendlytoml as toml


def get_local(*path):
    """Returns the given path relative to the location of this script"""
    return os.path.join(os.path.dirname(__file__), os.path.join(*path))


def template(*path):
    return get_local("templates", *path)    
    

IMAGE_PAGE_TEMPLATE_FILE = template("image_page.tpl")
DEFAULT_AUTHOR = os.environ.get("USER", "Unknown author")


def get_image_size(imagepath):
    """Returns the size of the given image"""
    img = Image.open(imagepath)
    return img.size


def create_epub_from_images(title, author, *image_paths):
    """Creates an ePub from the given list of image files"""
    if not image_paths:
        raise Exception("No images provided!")
    
    if author is None:
        author = DEFAULT_AUTHOR
    
    with open(IMAGE_PAGE_TEMPLATE_FILE) as f:
        chapter_template = f.read()
    
    
    def iter_images():
        """Iterates over the images and returns their name and bytes"""
        for image_path in image_paths:
            filename = os.path.basename(image_path)
            name = filename.rsplit(".", 1)[0]
            with open(image_path, "rb") as f:
                contents = f.read()
            yield (name, filename, contents)
        raise StopIteration
    
    
    def iter_chapters():
        """Iterates over the images and creates chapters pointing to the images"""
        for image_path in image_paths:
            filename = os.path.basename(image_path)
            title = filename.rsplit(".", 1)[0]
            try:
                width, height = get_image_size(image_path)
            except OSError:
                print("Error reading image: {!r}".format(image_path))
                continue
            text = chapter_template.format_map({
                "title": title,
                "filename": filename
            })
            yield (title, filename, text)
        
        raise StopIteration
    
    
    cover_path = image_paths[0]
    cover_type = cover_path.rsplit(".")[-1]
    with open(cover_path, "rb") as f:
        cover_bytes = f.read()
        
    metadata = {
        "tags": ["Image compilation"]
    }

    compile_epub(
        title, author, cover_type, cover_bytes, iter_chapters(), 
        images=iter_images(), path=None, metadata=metadata)


def create_epub_from_folder(folder, title=None, author=None):
    """Creates an ePub from the image files contained in the given folder"""
    endings = (".png", ".jpg", ".jpeg", ".svg", ".bmp", ".gif")
    def is_image(name):
        return (not name.startswith(".")) and name.lower().endswith(endings)
    
    def key(path):
        "(ischar, numval, strval)"
        name = os.path.basename(path).rsplit(".", 1)[0]
        if name.isdigit():
            return (0, int(name), name)
        else:
            return (1, 0, name)
    
    files = [os.path.join(folder, x) for x in os.listdir(folder) if is_image(x)]
    images = sorted(files, key=key)
    title = title if title else os.path.basename(folder)
    create_epub_from_images(title, author, *images)


def main(args=sys.argv[1:]):
    """Entry point"""
    description = "Creates an ePub file from the images in the given folder"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("folder")
    parser.add_argument("-t", "--title", default=None)
    parser.add_argument("-a", "--author", default=None)
    parsed = parser.parse_args(args)
    create_epub_from_folder(parsed.folder, title=parsed.title, author=parsed.author)

if __name__ == '__main__':
    main()
