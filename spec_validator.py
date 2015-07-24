# encoding: utf-8
import os
from validator import validate


def validate_spec(spec, directory=os.getcwd()):
    """Validates the given specification dictionary"""
    members = [
        "title",
        "author",
    ]
    paths = [
        "cover_file",
        "source_files",
    ]
    optpaths = [
        "description_file",
        "image_folders",
    ]
    valid, errors = validate(spec, members, paths=paths,
        optpaths=optpaths, directory=directory)

    if not valid:
        errortext = "Invalid Specification! Errors:\n- " + "\n- ".join(e for e in errors)
        raise Exception(errortext)
    return valid
