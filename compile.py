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


def get_local(*path):
    """Returns the given path relative to the location of this script"""
    return os.path.join(os.path.dirname(__file__), os.path.join(*path))


def template(*path):
    return get_local("templates", *path) 
    

# Globals
MARKDOWN_TEMPLATE_FILE = template("markdown.tpl")


def compile_epub(title, author, cover_type, cover_bytes, chapters, images=[], path=None, metadata={}):
    """Compiles an ePub from the given arguments.
    The path is where the ePub should be saved to 
    (or with a default name in the current direcory).
    The chapters should be an iterable of (title, filename, chapter_text) pairs.
    The images should be an iterable of (title, filename, bytes) pairs
    pairs"""
    if not path:
        path = title + " - " + author + ".epub"

    print("Compiling epub...")
    with Epub(
            title, author, path, cover_type, cover_bytes, 
            metadata=metadata) as epub:
        
        epub.add_cover(cover_type, cover_bytes)
        for (local_name, filename, text) in chapters:
            epub.add_chapter(local_name, filename, text)
            
        for (local_name, filename, image_bytes) in images:
            epub.add_image(local_name, filename, image_bytes)

    print("Done!")
    print("Saved ePub to {!r}".format(path))
    

def get_local(*path):
    """Returns the given path relative to the location of this script"""
    return os.path.join(os.path.dirname(__file__), os.path.join(*path))


def quick_load(*path):
    """Loads the text of a local file and closes it again"""
    fpath = get_local(*path)
    with open(fpath) as f:
        text = f.read()
    return text
    

# Make images downloaded through a Danish firefox version point locally
_pattern = re.compile(r'"[^"]*?-filer\/(.*?)"')
_replacer = lambda m: '"{}"'.format(m.groups(1)[0])
def clean_html(html):
    """Cleans up file references in downloaded pages"""
    return _pattern.sub(_replacer, html)


def split_and_compile(source_text):
    """Splits the source text into chapters and compiles each to html from
    markdown. Returns a list of (filename, content), and the list of these
    filenames"""
    # All this splitting makes it slow :c
    after_first_chapter = False
    for num, text in enumerate(source_text.split("\n# "), 1):
        # Use the first line (minus the markdown header marker) as the title
        start = 2 if text.startswith("# ") else 0
        chapter_name = text[start : text.find("\n")]
        name = "{}.html".format(chapter_name)
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

        template = quick_load(MARKDOWN_TEMPLATE_FILE)
        html = template.format_map({"text": "\n".join(lines)})
        yield (chapter_name, name, html)
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


def iter_load_chapters(directory, source_paths):
    """Yields the chapter tuples from loading the given text source paths.
    source_is_html toggles whether to interpret the text contents as html 
    or compile from them as markdown"""
    for path in (os.path.join(directory, p) for p in source_paths):
        source_text = load_source_text(path)
        base = os.path.basename(path)
        name = base.rsplit(".", 1)[0]
        if path.endswith((".html", ".xhtml")):
            text = clean_html(source_text)
            yield (name, base, text)
        elif path.endswith(".md"):
            yield from split_and_compile(source_text)
        else:
            yield (name, base, source_text)

    raise StopIteration


def iter_load_images(directory, images, image_folders=[]):
    """Loads and iterates over the images from the images and image folders 
    parts of the ePub specification file"""
    endings = (".png", ".jpg", ".jpeg", ".svg", ".bmp", ".gif")
    def is_image(name):
        return (not name.startswith(".")) and name.lower().endswith(endings)
    
    for name, relative_path in images.items():
        path = os.path.join(directory, relative_path)
        filename = os.path.basename(path)
        with open(path, "rb") as f:
            contents = f.read()
        yield (name, filename, contents)
        
    for folder in (os.path.join(directory, f) for f in image_folders):
        for dirpath, _, filenames in os.walk(folder):
            for filename in (f for f in filenames if is_image(f)):
                if filename not in images:
                    filepath = os.path.abspath(os.path.join(dirpath, filename))
                    name = filename.rsplit(".", 1)[0]
                    with open(filepath, "rb") as f:
                        contents = f.read()
                    yield (name, filename, contents)
                else:
                    print("! Duplicate image found: {!r}".format(filename))
    
    raise StopIteration


def compile_epub_from_specification(spec_dict, directory, target_path=None):
    """# Compiles an ebook in the ePub format from the given specification file
    # =============================================================
    # Example of a specification file for a book in the ePub format
    # =============================================================

    # Specification file for the compilation of an epub

    title 		 = "Test book"
    author 		 = "Jakob Lautrup Nysom"
    cover_file 	 = "test_cover.png"
    source_files = ["test_source.md", "test_image_page.html"]

    # Optional
    language	= "en"
    series		= "Test series"
    volume		= 1
    tags		= ["Horror", "Heartwarming", "Random",]
    description = "A book about the horrors related to testing of computer programs"

    # image_folders = ["folder_with_lots_of_images_to_include_automatically",]

    [image_files]
    image1 = "test_cover.png"
    """
    # Ensure that this can be done!
    validate_spec(spec_dict, directory)

    def get_local_to_spec(path):
        """Returns a path locally to the specfile"""
        return os.path.join(directory, path)

    title = spec_dict['title']
    author = spec_dict['author']
    
    if not target_path:
        target_path = os.path.abspath("{} - {}.epub".format(title, author))
    
    # Cover
    cover_path = get_local_to_spec(spec_dict['cover_file'])
    cover_type = cover_path.rsplit(".", 1)[-1]
    with open(cover_path, "rb") as f:
        cover_bytes = f.read()
    
    # Chapters
    files = (get_local_to_spec(f) for f in spec_dict['source_files'])
    chapters = iter_load_chapters(directory, files)
    
    # Images
    images = iter_load_images(
        directory,
        spec_dict.get("image_files", {}), 
        image_folders=spec_dict.get("image_folders", []))
    
    
    compile_epub(
        title, author, cover_type, cover_bytes, chapters, images=images, 
        path=target_path, metadata=spec_dict)
