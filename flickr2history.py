#!/usr/bin/python


__author__ = "pkolarov@gmail.com"

import dbhash,anydbm
import sys, os, shelve, logging,string
import flickr

user = None



#get one and only one photo for the given tags or None
#this works only if we previously tagged all the pics on Flickr with uploader tool automaticaly
#
#Plus delete images that contain the same TAGS !!!!
def getPhotoIDbyTag(tag):
  
    
    retries = 0
    photos = None
    while (retries < 3):
        try:
                logging.debug(user.id)
                photos = flickr.photos_search(user_id=user.id, auth=all, tags=tag,tag_mode='any')
                break
        except:
                logging.error("flickr2history: Flickr error while searching ....retrying")
                logging.error(sys.exc_info()[0])
                
        retries = retries + 1
        
    if (not photos or len(photos) == 0):
        logging.debug("flickr2history: No image in Flickr (yet) with tags %s (possibly deleted in Flickr by user)" % tag)
        return None
    
    logging.debug("flickr2history: Tag=%s found %d" % (tag, len(photos)))
    while (len(photos)>1):
        logging.debug( "flickr2history :Tag %s matches %d images!" % (tag, len(photos)))
        logging.debug("flickr2history: Removing other images")
        try:
            photos.pop().delete()
        except:
            logging.error("flickr2history: Flickr error while deleting duplicate image")
            logging.error(sys.exc_info()[0])
   
    return photos[0]

#store image reference in the history file if its not there yet and if we actually can
#find it on Flickr
def reshelf(images,  imageDir, historyFile):
     
     logging.debug('flickr2history: Started flickr2history')
     try:
         global user
         user = flickr.test_login()
         logging.debug(user.id)
     except:
         logging.error(sys.exc_info()[0])
         return None
        
     for image in images:
        image = image[len(imageDir):] #remove absolute directory
        uploaded = shelve.open( historyFile )   #its better to always reopen this file
        if ( not uploaded.has_key(str(image) ) ):
                  #each picture should have one id tag in the folder format with spaces replaced by # and starting with #
                  flickrtag = '#' + image.replace(' ','#')
                  photo = getPhotoIDbyTag(flickrtag)
                  logging.debug(image)
                  if(not photo):
                       uploaded.close()  # flush the DB file
                       continue
                  logging.debug("flickr2history: Reregistering %s photo in local history file" % image)
                  uploaded[ str(image)] = str(photo.id)
                  uploaded[ str(photo.id) ] =str(image)
                  uploaded.close()
    
