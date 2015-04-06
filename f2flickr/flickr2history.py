#!/usr/bin/python
"""
A way to recreate the history database of uploaded files from the photos stored
on flickr.
"""

__author__ = "pkolarov@gmail.com"

import logging
import shelve
import sys
import os
import f2flickr.flickr as flickr

def getPhotoIDbyTag(tag, user):
    """
    Get one and only one photo for the given tags or None
    this works only if we previously tagged all the pics on Flickr with
    uploader tool automaticaly

    Plus delete images that contain the same TAGS !!!!
    """
    retries = 0
    photos = None
    while (retries < 3):
        try:
            logging.debug(user.id)
            photos = flickr.photos_search(user_id=user.id, auth=all, tags=tag,
                                          tag_mode='any')
            break
        except:
            logging.error("flickr2history: Flickr error in search, retrying")
            logging.error(sys.exc_info()[0])

        retries = retries + 1

    if (not photos or len(photos) == 0):
        logging.debug("flickr2history: No image in Flickr (yet) with tags %s " +
                      "(possibly deleted in Flickr by user)", tag)
        return None

    logging.debug("flickr2history: Tag=%s found %d", tag, len(photos))
    while (len(photos)>1):
        logging.debug("flickr2history: Tag %s matches %d images!",
                      tag, len(photos))
        logging.debug("flickr2history: Removing other images")
        try:
            photos.pop().delete()
        except:
            logging.error("flickr2history: Flickr error while " +
                          "deleting duplicate image")
            logging.error(sys.exc_info()[0])

    return photos[0]

def convert_format(images, imageDir, historyFile):
    """
    Convert a history file from old format to new that allows updated local files
    to be synced.
    For each file, store the following information:
    - Photo ID from Flickr
    - Modification time
    - Size of file
    """
    logging.debug('flickr2history: Started convert_format')

    uploaded = shelve.open( historyFile )
    num_images=len(images)
    num_ok=0
    num_converted=0
    num_not_found=0
    for i,image in enumerate(images):
        if (i+1) % 1000 == 0:
            sys.stdout.write('.'); sys.stdout.flush()
        full_image_path=image
        # remove absolute directory
        image = str(image[len(imageDir):])
        if uploaded.has_key(image):
            if isinstance(uploaded[image], tuple):
                num_ok += 1
                continue
        logging.debug("Converting history data for photo %s", image)
        try:
            photo_id=uploaded[image]
        except KeyError:
            logging.debug('Photo %s cannot be found from history file' % image)
            num_not_found += 1
            continue
        try:
            stats = os.stat(full_image_path)
            file_mtime=stats.st_mtime
            file_size=stats.st_size
        except OSError:
            file_mtime = 0
            file_size = 0
        uploaded[ image] = ( photo_id, file_mtime, file_size )
        uploaded[ photo_id ] = image
        num_converted += 1
    sys.stdout.write('\n'); sys.stdout.flush()
    logging.info('num_images=%d num_ok=%d num_not_found=%d num_converted=%d' %
                     (num_images, num_ok, num_not_found, num_converted))
    uploaded.close()

def reshelf(images,  imageDir, historyFile):
    """
    Store image reference in the history file if its not there yet and if we
    actually can find it on Flickr.
    For each file, store the following information:
    - Photo ID from Flickr
    - Modification time
    - Size of file
    """

    logging.debug('flickr2history: Started reshelf')
    try:
        user = flickr.test_login()
        logging.debug(user.id)
    except:
        logging.error(sys.exc_info()[0])
        return None

    for image in images:
        # remove absolute directory
        full_image_path=image
        image = image[len(imageDir):]
        # its better to always reopen this file
        uploaded = shelve.open( historyFile )
        if uploaded.has_key(str(image)):
            if isinstance(uploaded[str(image)], tuple):
                uploaded.close()
                continue
        # each picture should have one id tag in the folder format with spaces
        # replaced by # and starting with #
        flickrtag = '#' + image.replace(' ','#')
        photo = getPhotoIDbyTag(flickrtag, user)
        logging.debug(image)
        logging.debug(photo)
        if not photo:
            uploaded.close()  # flush the DB file
            continue
        logging.debug("flickr2history: Reregistering %s photo "+
                      "in local history file", image)
        stats = os.stat(full_image_path)
        file_mtime=stats.st_mtime
        file_size=stats.st_size
        uploaded[ str(image)] = ( str(photo.id), file_mtime, file_size )
        uploaded[ str(photo.id) ] =str(image)
        uploaded.close()
