# encoding: utf-8

"""
Helps with the compilation of an e-book based on a lightly markupped plaintext file,
and a small specification file.
"""
import os
import re

import markdown
import chardet
from spec_validator import validate_spec
from epub import Epub


def compile_epub_with_items(title, author, cover_type, cover_bytes, chapters, images={}, path=None, metadata={}):
    """Compiles an ePub from the given arguments.
    The path is where the ePub should be saved to 
    (or with a default name in the current direcory).
    The chapters should be a list of (title, chapter_text) pairs.
    The images should be a dict of {file name in the zip archive : bytes} pairs"""
    if not path:
        path = title + " - " + author + ".epub"

    print("Compiling epub...")
    with Epub(
            title, author, target_path, cover_type, cover_bytes, 
            metadata=metadata) as epub:
        
        epub.add_cover(cover_type, cover_bytes)
        for (title, text) in chapters:
            epub.add_chapter(title, text)
            
        for (name, image_bytes) in images:
            epub.add_image(name, image_bytes)

    print("Done!")
    print("Saved ePub to {!r}".format(target_path))


"""
# =========================================
# Example of a specfile for the commandline
# =========================================

# Specification file for the compilation of an epub

title 		 = "Arifureta Shokugyou de Sekai Saikyou - Vol 1"
author 		 = "Chuuni Suki"
cover_file 	 = "Arifureta.png"
source_files = ["Arifureta vol1.txt",]

# Optional
language	= "en"
series		= "Arifureta"
volume		= 1
tags		= ["Web Novel", "MMORPG", "Fantasy", "Japanese"]
source		= "www.japtem.com"
description_file = "Arifureta description.txt"

[image_files]
#image1 = "/home/images/arifureta-image1.png"

"""


_pattern = re.compile(r'"[^"]*?-filer\/(.*?)"')
_replacer = lambda m: '"{}"'.format(m.groups(1)[0])
def clean_html(html):
    """Cleans up file references in downloaded pages"""
    return _pattern.sub(_replacer, html)

def split_and_compile(source_text, chapter_name):
    """Splits the source text into chapters and compiles each to html from
    markdown. Returns a list of (filename, content), and the list of these
    filenames"""
    # All this splitting makes it slow :c
    after_first_chapter = False
    for num, text in enumerate(source_text.split("\n# ")):
        name = "{}_split-{}.html".format(chapter_name, num)
        print("- Writing '{}'".format(name))
        lines = []

        line_started = False
        for line in text.split("\n"):
            # Add the header sign (#) that was removed by the splitting
            if after_first_chapter and not line_started:
                line = "# " + line

            if not line:
                # Preserve the space
                lines.append("<p></p>")

            else:
                # Get the markdown for this line
                lines.append(markdown.markdown(line))
            line_started = True

        template = "<html><head></head><body>\n{}\n</body></html>"
        html = template.format("\n".join(lines))
        yield (name, html)
        after_first_chapter = True

    raise StopIteration

def load_source_text(path):
    """Loads the text in the given source as utf-8"""
    with open(path, "rb") as f:
        source = f.read()
    try:
        return str(source, encoding="utf-8")
    except UnicodeDecodeError:
        encoding = chardet.detect(source)["encoding"]
        return str(source, encoding=encoding)


def create_parts(source_text, path, text_is_html):
    """Creates the chapters for a given source text, by either compiling it
    (if it is my blend of markdown) or cleaning it if it is HTML already"""
    chapter_name = os.path.basename(path).split(".")[0]
    if not text_is_html:
        print(": text is html : FALSE")
        return split_and_compile(source_text, chapter_name)
    else:
        print(": text is html : TRUE")
        text = clean_html(source_text)
        return [(chapter_name, text)]


def get_chapters(source_paths, source_is_html):
    for path in source_paths:
        source_text = load_source_text(path)
        text_is_html = source_is_html or (source_text[:6] == "<html>")
        text_parts = create_parts(source_text, path, text_is_html)


def add_images(images, image_folders, get_local_to_spec, zfile):
    """Adds images to the ePub from the given dict and folders.
    get_local_to_spec is the function of the same name"""
    # - Add the images from the given image folders
    endings = (".png", ".jpg", ".jpeg", ".svg", ".bmp", ".gif")
    def is_image(name):
        return (not name.startswith(".")) and name.lower().endswith(endings)

    for folder in image_folders:
        for dirpath, _, filenames in os.walk(folder):
            for filename in (f for f in filenames if is_image(f)):
                if filename not in images:
                    filepath = os.path.abspath(os.path.join(dirpath, filename))
                    images[filename] = filepath
                else:
                    print("! Duplicate image found: {!r}".format(filename))

    # - Add the separately specified images
    for image_file, local_name in images.items():
        path = get_local_to_spec(local_name)
        with open(path, "rb") as f:
            zfile.writestr(image_file, f.read())
        print("- Moved image '{}'".format(image_file))



def compile_epub(spec_dict, directory, target_path=None, source_is_html=False):
    """Compiles an ebook in the epub format from the given specification file"""
    # Ensure that this can be done!
    validate_spec(spec_dict, directory)

    def get_local_to_spec(path):
        """Returns a path locally to the specfile"""
        return os.path.join(directory, path)

    title = spec_dict['title']
    author = spec_dict['author']
    images = spec_dict.get("image_files", {})
    image_folders = spec_dict.get("image_folders", [])
    cover_path = get_local_to_spec(spec_dict['cover_file'])
    source_paths = [get_local_to_spec(f) for f in spec_dict['source_files']]
    
    if not target_path:
        target_path = get_local_to_spec(title + " - " + author + ".epub")

if __name__ == '__main__':
    print(create_content_page("derp", "hello.png", "world", ["a", "b"], {"description": "Some Crap I Found"}))