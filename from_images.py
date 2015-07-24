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


def create_epub_from_images(title, *images, author=DEFAULT_AUTHOR):
    """Creates an ePub from the given list of image files"""
    if not images:
        raise Exception("No images provided!")
    with open("image_page.tpl") as f:
        page_template = f.read()
    source_file = tempfile.NamedTemporaryFile("w", delete=False)
    "write the source text for the image stuff"
    image_files = {}
    for i, image_path in enumerate(images):
        try:
            width, height = get_image_size(image_path)
        except OSError:
            print("Error reading image: {!r}".format(image_path))
            continue
        base = os.path.basename(image_path).rsplit(".", 1)[0].replace(".", "_")
        name = base
        num = 1
        while base in image_files:  # Rename on conflict
            base = name + str(num)
            num += 1

        print("Adding {:04}: {!r}".format(i, base))
        image_files[base] = os.path.abspath(image_path)
        content = page_template.format(width, height, base)
        if image_files:  # After the first one
            source_file.write("<!--\n# -->")  # Split signal
        source_file.write(content)


    specs = {
        "title": title,
        "author": author,
        "cover_file": os.path.abspath(images[0]),
        "source_files": [source_file.name],
        "image_files": image_files
    }
    print("Specs:")
    toml.dump(specs)
    source_file.close()
    print("\n\n")
    print("=" * 60)
    print("Source:")
    # The directory doesn't matter with absolute paths
    directory = os.getcwd()

    compile_epub(specs, directory)

    os.remove(source_file.name)
    print("source_file exists: {}".format(os.path.exists(source_file.name)))

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
    #parser = argparse.ArgumentParser()

    #parsed = parser.parse_args(args)
    create_epub_from_folder("/Users/jakoblautrupnysom/Documents/Personlig/Odd/vacation")

if __name__ == '__main__':
    main()
