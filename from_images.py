# encoding: utf-8
# Created by Jabok @ Thursday July 24th 2015
import os
import sys
import argparse
import tempfile
from PIL import Image

from compile import compile_epub
import friendlytoml as toml


DEFAULT_AUTHOR = os.environ.get("USER", "Unknown author")


def get_image_size(imagepath):
    """Returns the size of the given image"""
    img = Image.open(imagepath)
    return img.size


def create_epub_from_images(title, *image_paths, author=DEFAULT_AUTHOR):
    """Creates an ePub from the given list of image files"""
    if not image_paths:
        raise Exception("No images provided!")
    
    with open("title.tpl") as f:
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
                
            yield (title, filename, chapter_template.format(width, height, name))
        
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


def create_epub_from_folder(folder):
    """Creates an ePub from the image files contained in the given folder"""
    endings = (".png", ".jpg", ".jpeg", ".svg", ".bmp", ".gif")
    def is_image(name):
        return (not name.startswith(".")) and name.lower().endswith(endings)
    images = (os.path.join(folder, x) for x in os.listdir(folder) if is_image(x))
    title = os.path.basename(folder)
    create_epub_from_images(title, *images)

def main(args=sys.argv[1:]):
    """Entry point"""
    description = "Creates an ePub file from the images in the given folder"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("folder")
    parsed = parser.parse_args(args)
    create_epub_from_folder(parsed.folder)

if __name__ == '__main__':
    main()
