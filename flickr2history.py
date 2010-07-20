#!/usr/bin/python


__author__ = "pkolarov@gmail.com"

import sys, os, shelve, logging,string
import flickr

user = None

#remove items in checked from seq
def removeTags(seq):  
    # order preserving 
    checked = ["and","in","at","a","the","of","an", "&", "to", "on", "-","+","&" ]
    out =[]
    for e in seq: 
        if e not in checked: 
            out.append(e) 
    return out

#get one and only one photo for the given tags or None
#this works only if we previously tagged all the pics on Flickr with uploader tool automaticaly
#
#Plus delete images that contain the same TAGS !!!!
def getPhotoIDbyTag(tag):
    tags=tag.split()
     #remove multiple whitespaces,and  "and","in","at","a","the","of","an", "&" etc.
    tags = removeTags(tags)
    out=string.join(tags,",")
    retries = 0
    photos = None
    while (retries < 3):
        try:
                logging.debug(user.id)
                photos = flickr.photos_search(user_id=user.id, auth=all, tags=out,tag_mode='all')
                break
        except:
                logging.error("Flickr error while searching ....retrying")
                logging.error(sys.exc_info()[0])
                
        retries = retries + 1
        
    if (not photos or len(photos) == 0):
        logging.error("No image in Flickr with tags %s (something failed during its upload)" % out)
        return None
    
    logging.debug("Tag=%s found %d" % (out, len(photos)))
    while (len(photos)>1):
        logging.debug( "Tag %s matches %d images!" % (out, len(photos)))
        logging.debug("Removing other images")
        try:
            photos.pop().delete()
        except:
            logging.error("Flickr error while deleting image")
            logging.error(sys.exc_info()[0])
   
    return photos[0]

#store image reference in the history file if its not there yet and if we actually can
#find it on Flickr
def reshelf(images,  imageDir, historyFile):
     
     logging.debug('Started flickr2history')
     try:
         global user
         user = flickr.test_login()
         logging.debug(user.id)
     except:
         logging.error(sys.exc_info()[0])
         return None
        
     for image in images:
        image = image[len(imageDir):] #remove absolute directory
        uploaded = shelve.open( historyFile )
        if ( not uploaded.has_key(str(image) ) ):
                  photo = getPhotoIDbyTag(image)
                  logging.debug(image)
                  if(not photo):
                       uploaded.close()
                       continue
                  #logging.debug(photo.id)
                  uploaded[ str(image)] = str(photo.id)
                  uploaded[ str(photo.id) ] =str(image)
                  uploaded.close()
    
