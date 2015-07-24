# encoding: utf-8
import os
from create_epub import split_and_compile, compile_epub, validate_spec, quick_load


def test_split():
    source = "test_source.md"
    files = split_and_compile(quick_load(source), source)
    for (name, html) in files:
        with open(name, "w") as f:
            f.write(html)


def test_compile():
    spec = {
        "title": "The Test of the ePub Creator",
        "author": "Jabok Partulu Nymos",
        "cover_file": "test_cover.png",
        "source_file": "test_source.md"
    }
    compile_epub(spec, os.getcwd())


def test_validate():
    valid_spec = {
        "title": "The Test of the ePub Creator",
        "author": "Jabok Partulu Nymos",
        "cover_file": "test_cover.png",
        "source_file": "test_source.md",
        "language": "English",
        "tags": ["fun", "programming", "ePub", "jabok"]
    }
    validate_spec(valid_spec)
    print("Valid test: PASSED")

    invalid_spec = valid_spec
    invalid_spec.update({
        "cover_file": "missing.png",
        "source_file": "not_there.md",
        "description_file": "yeah_right.txt"
    })
    try:
        validate_spec(invalid_spec)
        print("NO ERRORS: THIS IS BAD!")
    except Exception as e:
        print("Exception!")
        print(e)
        print("Invalid test: PASSED")
