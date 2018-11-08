import os
from uuid import UUID

from django.conf import settings
from django.core.mail import send_mail

from celery import shared_task
from PIL import Image

from sa_helper import Session
from users.mappings import User
from .mappings import Photo



@shared_task()
def create_thumbnails(filename):
    sizes = settings.THUMBNAIL_SIZES
    basename, ext = os.path.splitext(filename)
    result = {}
    for size_name, size in sizes.items():
        new_filename = '{}.{}{}'.format(basename, size_name, ext)
        im = Image.open(os.path.join(settings.MEDIA_ROOT, filename))
        im.thumbnail(size)
        im.save(os.path.join(settings.MEDIA_ROOT, new_filename))
        result[size_name] = new_filename
    result['fullsize'] = filename
    return result

@shared_task()
def store_thumbnail_paths(filenames, photo_id):
    sa_session = Session()
    photo = sa_session.query(Photo).filter(Photo.id == UUID(photo_id)).one()
    photo.thumbnails = filenames
    sa_session.commit()
    return filenames

@shared_task()
def send_email(filenames, user_id):
    sa_session = Session()
    user = sa_session.query(User).filter(User.id == UUID(user_id)).one()
    message = '''
Dear {first_name} {last_name}
Your photo is successfully uploaded!
Please use these urls:
\n'''.format(first_name=user.name, last_name=user.last_name)
    urls = ('{name}: {site_url}{media_url}{filename}'
                .format(name=size_name,
                        site_url=settings.SITE_URL_IN_EMAIL,
                        media_url=settings.MEDIA_URL,
                        filename=filename)
            for size_name, filename in filenames.items())
    message+='\n'.join(urls)
    send_mail(
        'New photo uploaded',
        message,
        settings.NEW_PHOTO_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

def process_upload(photo_id, user_id, filename):
    chain = (create_thumbnails.s(filename)
             | store_thumbnail_paths.s(photo_id)
             | send_email.s(user_id))
    chain.apply_async()
