# coding: utf-8
# Created by Jabok @ January 31st 2015
# scrape_epub.py
"""
Scrapes the content of an ePub for easy editing and repackaging
"""
import os
import sys
import xml.etree.ElementTree as ET
import zipfile
from argparse import ArgumentParser

import toml
from bs4 import BeautifulSoup
from bs4.element import NavigableString

# Globals
CONTAINER_PATH = "META-INF/container.xml"
IMAGE_EXTENSIONS = (
    ".png",
    ".jpg",
    ".jpeg"
)

# Other stuff

def findall(source_node, tag):
    """Iterates over all tags of the given type below the given node"""
    for item in source_node.iter():
        if item.tag.endswith(tag):
            yield item

def find(source_node, tag):
    """Returns the first instance of tag below the given node"""
    for item in source_node.iter():
        if item.tag.endswith(tag):
            return item

ITALIC_TAGS = set(["i", "em"])
def format_item(tag):
    """Formats an item on a html line for markdown"""
    bucket = []
    # Simple string
    if type(tag) == NavigableString:
        return [str(tag)]
        
    # Image
    elif tag.name == "img":
        return ["![{0}]({0})".format(tag["src"])]
    # Text tag / composite
    else:
        wrapper = ""
        # Italic
        if tag.name in ITALIC_TAGS:
            wrapper = "*"
        elif tag.name == "b":
            wrapper = "**"
        
        if wrapper:
            bucket.append(wrapper)
        
        contents = tag.contents
        if len(contents) == 1 and wrapper:  # single inner italic or bold
            item = contents[0]
            if type(item) == NavigableString:
                bucket.append(str(item).strip())
            else:
                bucket += format_item(item)
        else:
            for item in contents:
                bucket += format_item(item)
        
        if wrapper:
            bucket.append(wrapper)
    
    return bucket

def scrape_metadata(zip_archive):
    """Scrapes the metadata of an ePub from a given open ZipFile object"""
    # Locate the .opf file (this is just for compatibility, I think?)
    container_root = ET.fromstring(zip_archive.read(CONTAINER_PATH))
    
    meta_path = find(container_root, "rootfile").get("full-path")
    
    # Open the opf file
    meta_root = ET.fromstring(zip_archive.read(meta_path))
    metadata_root = find(meta_root, "metadata")
    
    def get(tag, default=None):
        items = [item.text for item in findall(metadata_root, tag)]
        if not items:
            return default
        else:
            if len(items) == 1:
                return items[0]
            else:
                return items    
    
    title = get("title", "") 
    tags = get("subject", [])
    author = get("creator", "")
    language = get("language", "")
    
    # Map the spine Ids to item references and find the images in the ePub
    item_map = {}
    images = []
    manifest = find(meta_root, "manifest")
    for item in findall(manifest, "item"):
        item_id = item.get("id")
        reference = item.get("href")
        item_map[item_id] = reference
    
    cover_file = item_map.get("cover", None)
    
    spine_list = []
    spine = find(meta_root, "spine")
    for ref in findall(spine, "itemref"):
        idref = ref.get("idref")
        if idref != "titlepage": # Ignore the title page, since I create that myself
            spine_list.append(item_map[idref])
    
    # Grab the images
    print("Saving images...")
    image_paths = {}  # How to locate the images again
    for item in zip_archive.infolist():
        if item.filename.lower().endswith(IMAGE_EXTENSIONS):
            image = item.filename
            image_path = title + "-" + image
            with open(image_path, "wb") as f:
                f.write(zip_archive.read(image))
                print("- Saved image to '{}'".format(image_path))
            image_paths[image] = image_path
    
    # Create simple markdown from the HTML source
    text = "\n".join(spine_list)
    
    # Scrape and write the HTMl => Markdown
    print("Writing source file...")
    source_path = title + "-source.md"
    with open(source_path, "w") as f:
        for num, source_file in enumerate(spine_list):
            soup = BeautifulSoup(zip_archive.read(source_file))
            # For each line in a nice eBook
            for line_num, tag in enumerate(soup.body.find_all(recursive=False)):
                
                # A title of some sort
                if tag.name.startswith("h"):
                    # New file (prepare for a split here) => automatic h1 (for now)
                    if num and line_num == 0:
                        line_parts = ["# ", tag.text]
                    
                    else:
                        level = int(tag.name[1:])
                        line_parts = [("#"*level) + " ", tag.text]
            
                # Just some text (maybe with images)
                else:
                    line_parts = format_item(tag)
            
                # Strip the line
                if line_parts:
                    line_parts[0] = line_parts[0].lstrip()
                    line_parts[-1] = line_parts[-1].rstrip()
                
                # Write the line to the output file
                line_parts.append("\n")
                f.write("".join(line_parts))
            print("- Wrote '{}'".format(source_file))
    
    print("Saved the source to '{}'".format(source_path))
    
    cover_path = title + "-cover." + cover_file.split(".")[-1]
    meta = {
        "title": title,
        "author": author,
        "cover_file": cover_path,
        "source_file": source_path,
        "tags": tags,
        "image_files": image_paths
    }
    if language:
        meta["language"] = language

    # Write the metadata
    spec_path = title + "-spec.toml"
    with open(spec_path, "w") as f:
        toml.dump(meta, f)
        print("Saved the spec to '{}'".format(spec_path))

def scrape_epub(filepath):
    """Scrapes everything out of that epub /yay/"""
    with zipfile.ZipFile(filepath) as file:
        scrape_metadata(file)

def main(args=sys.argv[1:]):
    """Entry point"""
    parser = ArgumentParser()
    parser.add_argument("epub", help="The path of the ePub to scrape")
    
    parsed = parser.parse_args(args)
    scrape_epub(parsed.epub)

if __name__ == '__main__':
    main()