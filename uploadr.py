#!/usr/bin/env python

import dbhash,anydbm
import sys, time, os, urllib2, shelve, string, logging, flickr, re
import xmltramp, mimetools, mimetypes, md5, webbrowser, exif, flickr2history, tags2set, deleteAll
from ConfigParser import *

#
#   uploadr.py
#
#   Upload images placed within a directory to your Flickr account.
#
#   Requires:
#       xmltramp http://www.aaronsw.com/2002/xmltramp/
#       flickr account http://flickr.com
#
#   Inspired by:
#        http://micampe.it/things/flickruploadr
#
#
#   September 2005
#   Cameron Mallory   cmallory/berserk.org
#
#   This code has been updated to use the new Auth API from flickr.
#
#   You may use this code however you see fit in any form whatsoever.
#
#   2009 Peter Kolarov  -  Updated with fixes and new functionality 
#
#

configdict = ConfigParser()
configdict.read('uploadr.ini')



#
# Location to scan for new images
#
IMAGE_DIR = configdict.defaults()['imagedir']
#
#   Flickr settings
#
FLICKR = {"title": "",
        "description": "",
        "tags": "auto-upload",
        "is_public": configdict.defaults()['public'],
        "is_friend": configdict.defaults()['friend'],
        "is_family": configdict.defaults()['family'] }

#
#   File we keep the history of uploaded images in.
#
HISTORY_FILE = configdict.defaults()['history_file']

#Kodak cam EXIF tag  keyword
XPKEYWORDS = 'Image XPKeywords'






##
##  You shouldn't need to modify anything below here
##
FLICKR["secret" ] = "13c314caee8b1f31"
FLICKR["api_key" ] = "91dfde3ed605f6b8b9d9c38886547dcf"
flickr.API_KEY = FLICKR["api_key" ]
flickr.API_SECRET =FLICKR["secret" ] 
flickr.tokenFile= ".flickrToken"
flickr.AUTH = True




class APIConstants:
    base = "http://flickr.com/services/"
    rest   = base + "rest/"
    auth   = base + "auth/"
    upload = base + "upload/"

    token = "auth_token"
    secret = "secret"
    key = "api_key"
    sig = "api_sig"
    frob = "frob"
    perms = "perms"
    method = "method"

    def __init__( self ):
       pass

api = APIConstants()

class Uploadr:
    token = None
    perms = ""
    TOKEN_FILE = flickr.tokenFile

    def __init__( self ):
        self.token = self.getCachedToken()



    """
    Signs args via md5 per http://www.flickr.com/services/api/auth.spec.html (Section 8)
    """
    def signCall( self, data):
        keys = data.keys()
        keys.sort()
        foo = ""
        for a in keys:
            foo += (a + data[a])

        f = FLICKR[ api.secret ] + api.key + FLICKR[ api.key ] + foo
        #f = api.key + FLICKR[ api.key ] + foo
        return md5.new( f ).hexdigest()

    def urlGen( self , base,data, sig ):
        foo = base + "?"
        for d in data:
            foo += d + "=" + data[d] + "&"
        return foo + api.key + "=" + FLICKR[ api.key ] + "&" + api.sig + "=" + sig


    #
    #   Authenticate user so we can upload images
    #
    def authenticate( self ):
        #print "Getting new Token"
        self.getFrob()
        self.getAuthKey()
        self.getToken()
        self.cacheToken()

    """
    flickr.auth.getFrob

    Returns a frob to be used during authentication. This method call must be
    signed.

    This method does not require authentication.
    Arguments

    api.key (Required)
    Your API application key. See here for more details.
    """
    def getFrob( self ):
        d = {
            api.method  : "flickr.auth.getFrob"
            }
        sig = self.signCall( d )
        url = self.urlGen( api.rest, d, sig )
        try:
            response = self.getResponse( url )
            if ( self.isGood( response ) ):
                FLICKR[ api.frob ] = str(response.frob)
            else:
                self.reportError( response )
        except:
            print "Error getting frob:" , str( sys.exc_info() )
            logging.error(sys.exc_info())

    """
    Checks to see if the user has authenticated this application
    """
    def getAuthKey( self ):
        d =  {
            api.frob : FLICKR[ api.frob ],
            api.perms : "delete"
            }
        sig = self.signCall( d )
        url = self.urlGen( api.auth, d, sig )
        ans = ""
        try:
            webbrowser.open( url )
            ans = raw_input("Have you authenticated this application? (Y/N): ")
        except:
            print str(sys.exc_info())
        if ( ans.lower() == "n" ):
            print "You need to allow this program to access your Flickr site."
            print "A web browser should pop open with instructions."
            print "After you have allowed access restart uploadr.py"
            sys.exit()

    """
    http://www.flickr.com/services/api/flickr.auth.getToken.html

    flickr.auth.getToken

    Returns the auth token for the given frob, if one has been attached. This method call must be signed.
    Authentication

    This method does not require authentication.
    Arguments

    NTC: We need to store the token in a file so we can get it and then check it insted of
    getting a new on all the time.

    api.key (Required)
       Your API application key. See here for more details.
    frob (Required)
       The frob to check.
    """
    def getToken( self ):
        d = {
            api.method : "flickr.auth.getToken",
            api.frob : str(FLICKR[ api.frob ])
        }
        sig = self.signCall( d )
        url = self.urlGen( api.rest, d, sig )
        try:
            res = self.getResponse( url )
            if ( self.isGood( res ) ):
                self.token = str(res.auth.token)
                self.perms = str(res.auth.perms)
                self.cacheToken()
            else :
                self.reportError( res )
        except:
            print str( sys.exc_info() )
            logging.error(sys.exc_info())

    """
    Attempts to get the flickr token from disk.
    """
    def getCachedToken( self ):
        if ( os.path.exists( self.TOKEN_FILE )):
            return open( self.TOKEN_FILE ).read()
        else :
            return None



    def cacheToken( self ):
        try:
            open( self.TOKEN_FILE , "w").write( str(self.token) )
        except:
            print "Issue writing token to local cache " , str(sys.exc_info())
            logging.error(sys.exc_info())

    """
    flickr.auth.checkToken

    Returns the credentials attached to an authentication token.
    Authentication

    This method does not require authentication.
    Arguments

    api.key (Required)
        Your API application key. See here for more details.
    auth_token (Required)
        The authentication token to check.
    """
    def checkToken( self ):
        if ( self.token == None ):
            return False
        else :
            d = {
                api.token  :  str(self.token) ,
                api.method :  "flickr.auth.checkToken"
            }
            sig = self.signCall( d )
            url = self.urlGen( api.rest, d, sig )
            try:
                res = self.getResponse( url )
                if ( self.isGood( res ) ):
                    self.token = res.auth.token
                    self.perms = res.auth.perms
                    return True
                else :
                    self.reportError( res )
            except:
                print str( sys.exc_info() )
                logging.error(sys.exc_info())
            return False


    def upload( self ):
        print HISTORY_FILE
        self.uploaded = shelve.open( HISTORY_FILE )
        newImages = self.grabNewImages()
        
        for image in newImages:
            self.uploadImage( image )
        

#get all images in folders and subfolders which match extensions below
    def grabNewImages( self ):
        images = []
        foo = os.walk( IMAGE_DIR )
        for data in foo:
            (dirpath, dirnames, filenames) = data
            for f in filenames :
                ext = f.lower().split(".")[-1]
                if ( ext == "jpg" or ext == "gif" or ext == "png" or ext == "avi" or ext == "mov"):
                    images.append( os.path.normpath( dirpath + "/" + f ) )
        images.sort()
        return images


    def uploadImage( self, image ):
        folderTag = image[len(IMAGE_DIR):]
        #print folderTag
        #return
        if ( not self.uploaded.has_key( folderTag ) ):

            try:
                logging.debug( "Getting EXIF for %s" % image)
                f = open(image, 'rb')
                exiftags = exif.process_file(f)
                f.close()
                #print exiftags[XPKEYWORDS]

                
                #print folderTag
                #make one tag equal to original file path with spaces replaced by # and start it with # (for easier recognition) since space is used as TAG separator by flickr
                # this is needed for later syncing flickr with folders 
                realTags  = folderTag.replace('\\',' ')   # look for / or \ or _ or .  and replace them with SPACE to make real Tags 
                realTags =  realTags.replace('/',' ')   # these will be the real tags ripped from folders
                realTags =  realTags.replace('_',' ')
                realTags =  realTags.replace('.',' ')  
                picTags = '#' + folderTag.replace(' ','#') + ' ' + realTags

                if exiftags == {}:
                   logging.debug( 'NO_EXIF_HEADER for %s' % image)
                else:
                   if XPKEYWORDS in exiftags:  #look for additional tags in EXIF to tag picture with
                            if len(exiftags[XPKEYWORDS].printable) > 4:
                                picTags += exif.make_string( eval(exiftags[XPKEYWORDS].printable)).replace(';',' ')
                
                #print picTags
                logging.debug( "Uploading image %s" % image)
                photo = ('photo', image, open(image,'rb').read())


                d = {
                    api.token   : str(self.token),
                    api.perms   : str(self.perms),
                    "tags"      : str(picTags),
                    "is_public" : str( FLICKR["is_public"] ),
                    "is_friend" : str( FLICKR["is_friend"] ),
                    "is_family" : str( FLICKR["is_family"] )
                }
                sig = self.signCall( d )
                d[ api.sig ] = sig
                d[ api.key ] = FLICKR[ api.key ]
                url = self.build_request(api.upload, d, (photo,))
                xml = urllib2.urlopen( url ).read()
                res = xmltramp.parse(xml)
                if ( self.isGood( res ) ):
                    logging.debug( "successful.")
                    self.logUpload( res.photoid, folderTag )
                else :
                    print "problem.."
                    self.reportError( res )
            except:
                logging.error(sys.exc_info())


    def logUpload( self, photoID, imageName ):
        
        photoID = str( photoID )
        imageName = str( imageName )
        self.uploaded[ imageName ] = photoID
        self.uploaded[ photoID ] = imageName
        self.uploaded.close()
        self.uploaded = shelve.open( HISTORY_FILE )

    #
    #
    # build_request/encode_multipart_formdata code is from www.voidspace.org.uk/atlantibots/pythonutils.html
    #
    #
    def build_request(self, theurl, fields, files, txheaders=None):
        """
        Given the fields to set and the files to encode it returns a fully formed urllib2.Request object.
        You can optionally pass in additional headers to encode into the opject. (Content-type and Content-length will be overridden if they are set).
        fields is a sequence of (name, value) elements for regular form fields - or a dictionary.
        files is a sequence of (name, filename, value) elements for data to be uploaded as files.
        """
        content_type, body = self.encode_multipart_formdata(fields, files)
        if not txheaders: txheaders = {}
        txheaders['Content-type'] = content_type
        txheaders['Content-length'] = str(len(body))

        return urllib2.Request(theurl, body, txheaders)

    def encode_multipart_formdata(self,fields, files, BOUNDARY = '-----'+mimetools.choose_boundary()+'-----'):
        """ Encodes fields and files for uploading.
        fields is a sequence of (name, value) elements for regular form fields - or a dictionary.
        files is a sequence of (name, filename, value) elements for data to be uploaded as files.
        Return (content_type, body) ready for urllib2.Request instance
        You can optionally pass in a boundary string to use or we'll let mimetools provide one.
        """
        CRLF = '\r\n'
        L = []
        if isinstance(fields, dict):
            fields = fields.items()
        for (key, value) in fields:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            L.append(value)
        for (key, filename, value) in files:
            filetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append('Content-Type: %s' % filetype)
            L.append('')
            L.append(value)
        L.append('--' + BOUNDARY + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % BOUNDARY        # XXX what if no files are encoded
        return content_type, body


    def isGood( self, res ):
        if ( not res == "" and res('stat') == "ok" ):
            return True
        else :
            return False


    def reportError( self, res ):
        logging.error(res)
        try:
            print "Error:", str( res.err('code') + " " + res.err('msg') )
        except:
            print "Error: " + str( res )

    """
    Send the url and get a response.  Let errors float up
    """
    def getResponse( self, url ):
        xml = urllib2.urlopen( url ).read()
        return xmltramp.parse( xml )



if __name__ == "__main__":
        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='debug.log',
                    filemode='w')
        logging.debug('Started')
        console = logging.FileHandler('error.log')
        console.setLevel(logging.ERROR)
        logging.getLogger('').addHandler(console)
        
        flickr = Uploadr()
        if ( not flickr.checkToken() ):
            flickr.authenticate()

        #see if we need to wipe flickr account first
     
        if(configdict.defaults()['remove_all_pics_first'].startswith('true')):
            deleteAll.deleteAllPics()
            os._exit(1) ## STOP HERE after deleting all media so user has chance to turn off switch before next start

        images = flickr.grabNewImages()
        #this is just double checking if everything is on Flickr what is in the history file
	# in another words it will restore history file if deleted by comparing flickr with folders
        flickr2history.reshelf(images, IMAGE_DIR, HISTORY_FILE)

	#uploads all images that are in folders and not in history file        
        flickr.upload()  #uploads all new images to flickr

        
        #this will organize uploaded files into sets with the names according to tags
        tags2set.createSets( HISTORY_FILE)
