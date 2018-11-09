from django.core.files.storage import FileSystemStorage

import uuid
import os.path

def generate_uuid4_filename(filename):
    """
    Generates a uuid4 (random) filename, keeping file extension

    :param filename: Filename passed in. In the general case, this will
                     be provided by django-ckeditor's uploader.
    :return: Randomized filename in urn format.
    :rtype: str
    """
    discard, ext = os.path.splitext(filename)
    basename = str(uuid.uuid4())
    return ''.join((basename, ext))

def save_uploaded_photo(file):
    storage = FileSystemStorage()
    filename = generate_uuid4_filename(file.name)
    storage.save(filename, file)
    return filename
