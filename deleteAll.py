#!/usr/bin/python

import dbhash,anydbm
import sys, os, shelve, logging,string
from ConfigParser import *
import flickr

existingSets = None
user = None
configdict = ConfigParser()
configdict.read('uploadr.ini')
deleteAll = configdict.defaults()['remove_all_pics_first'] #set to true if Sets should be called only by the name of the last subfolder


def deleteAllPics( ):
        
        global user

        try:
             user = flickr.test_login()
             logging.debug(user.id)
        except:
            logging.error(sys.exc_info()[0])
            return None

        if(deleteAll.startswith('true') == False):
            return #check again to be sure if to go one

        logging.debug('deleteAll: Started Delete')
        retries = 0
        
        #this may take very long time !!!!
        while (retries < 3):
            try:
                    photos = []
                    logging.debug(user.id)
                    np = flickr.photos_search_pages(user_id=user.id, auth=all, per_page="500")
                    numPages = int(np)
                    i = 1
                    logging.debug("found %d num pages" % numPages)
                    while ( numPages > 0):
                        spage = str(i)
                        photos.extend(flickr.photos_search(user_id=user.id, auth=all, per_page="500", page=spage))
                        logging.debug( "added %d page to %d pic" % (i, len(photos)))
                        
                        numPages = numPages - 1
                        i = i + 1
                        
                    logging.debug( "got all %d pics to delete" % len(photos))
                    break
            except:
                    logging.error("deleteAll: Flickr error while searching ....retrying")
                    logging.error(sys.exc_info()[0])
                    
            retries = retries + 1
            
        if (not photos or len(photos) == 0):
            logging.debug("deleteAll: No files in Flickr to delete" )
            return None

        logging.debug("deleteAll: found %d media files to delete" % (len(photos)))
        while (len(photos)>1):
            try:
                photos.pop().delete()
                print "deleting pic " 
                logging.debug("deleteAll: Removed one image... %d images to go" % (len(photos)))

            except:
                logging.error("deleteAll: Flickr error while deleting image")
                logging.error(sys.exc_info()[0])

        logging.debug("deleteAll: DONE DELETING - NOTHING ELSE TO DO - EXITING")
        os._exit(1)    
