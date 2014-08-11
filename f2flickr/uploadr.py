#!/usr/bin/env python
"""
Upload images placed within a directory to your Flickr account.

Requires:
    flickr account http://flickr.com

Inspired by:
     http://micampe.it/things/flickruploadr


September 2005
Cameron Mallory   cmallory/berserk.org

This code has been updated to use the new Auth API from flickr.

You may use this code however you see fit in any form whatsoever.

2009 Peter Kolarov  -  Updated with fixes and new functionality
"""

from hashlib import md5
import logging
import glob
import mimetools
import mimetypes
import os
import re
import shelve
import sys
import urllib2
import webbrowser
import exifread
import string
from datetime import timedelta, datetime, time, date, tzinfo
from itertools import groupby
from os.path import dirname
import calendar

import f2flickr.flickr as flickr
import f2flickr.tags2set as tags2set
from f2flickr.configuration import configdict
from flickr2history import convert_format
from xml.dom import minidom

#
# Location to scan for new images
#
IMAGE_DIR = configdict.get('imagedir')
#
#   Flickr settings
#
FLICKR = {"title": "",
        "description": "",
        "tags": "auto-upload",
        "hidden": configdict.get('hidden', 2),
        "is_public": configdict.get('public'),
        "is_friend": configdict.get('friend'),
        "is_family": configdict.get('family') }

#
#   File we keep the history of uploaded images in.
#
HISTORY_FILE = configdict.get('history_file')

#Kodak cam EXIF tag  keyword
XPKEYWORDS = 'Image XPKeywords'

# file extensions that will be uploaded (compared as lower case)
ALLOWED_EXT = set('''
jpg
jpeg
gif
png
avi
mp4
mov
mpg
mpeg
'''.split())

##
##  You shouldn't need to modify anything below here
##
FLICKR["secret" ] = configdict.get('secret', '13c314caee8b1f31')
FLICKR["api_key" ] = configdict.get('api_key', '91dfde3ed605f6b8b9d9c38886547dcf')
flickr.API_KEY = FLICKR["api_key" ]
flickr.API_SECRET = FLICKR["secret" ]
flickr.tokenFile = ".flickrToken"
flickr.AUTH = True

def isGood(res):
    """
    Returns True if the response was OK.
    """
    return not res == "" and res.stat == "ok"

def getResponse(url):
    """
    Send the url and get a response.  Let errors float up
    """
    data = flickr.unmarshal(minidom.parse(urllib2.urlopen(url)))
    # pylint: disable=E1101
    return data.rsp

def reportError(res):
    """
    logs the error from the xml result and prints it too
    """
    try:
        err = "Error:", str( res.err.code + " " + res.err.msg )
    except AttributeError:
        err = "Error: " + str( res )
    logging.error(err)
    print err

#
# buildRequest/encodeMultipartFormdata code is from
# http://www.voidspace.org.uk/atlantibots/pythonutils.html
#
def encodeMultipartFormdata(fields, files):
    """ Encodes fields and files for uploading.
    fields is a sequence of (name, value) elements for regular form fields - or a dictionary.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files.
    Return (contenttype, body) ready for urllib2.Request instance
    You can optionally pass in a boundary string to use or we'll let mimetools provide one.
    """
    boundary = '-----'+mimetools.choose_boundary()+'-----'
    crlf = '\r\n'
    L = []
    if isinstance(fields, dict):
        fields = fields.items()
    for (key, value) in fields:
        L.append('--' + boundary)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        filetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        L.append('--' + boundary)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % filetype)
        L.append('')
        L.append(value)
    L.append('--' + boundary + '--')
    L.append('')
    body = crlf.join(L)
    contenttype = 'multipart/form-data; boundary=%s' % boundary
    return contenttype, body

def buildRequest(theurl, fields, files):
    """
    Given the fields to set and the files to encode it returns a fully formed urllib2.Request object.
    You can optionally pass in additional headers to encode into the opject. (Content-type and Content-length will be overridden if they are set).
    fields is a sequence of (name, value) elements for regular form fields - or a dictionary.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files.
    """
    contenttype, body = encodeMultipartFormdata(fields, files)
    txheaders = {}
    txheaders['Content-type'] = contenttype
    txheaders['Content-length'] = str(len(body))
    return urllib2.Request(theurl, body, txheaders)

class APIConstants:
    base = "https://flickr.com/services/"
    rest   = base + "rest/"
    auth   = base + "auth/"
    upload = "https://up.flickr.com/services/upload/"

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

def signCall(data):
    """
    Signs args via md5 per Section 8 of
    http://www.flickr.com/services/api/auth.spec.html
    """
    keys = data.keys()
    keys.sort()
    args = ""
    for key in keys:
        args += (key + data[key])

    tohash = FLICKR[ api.secret ] + api.key + FLICKR[ api.key ] + args
    return md5(tohash).hexdigest()


def urlGen(base, data):
    """
    Creates the url from the template
    base/?key=value...&api_key=key&api_sig=sig
    """
    sig = signCall(data)
    data[api.key] = FLICKR[api.key]
    data[api.sig] = sig
    query = '&'.join(key+'='+value for key, value in data.iteritems())
    return base + "?" + query

class Uploadr:
    token = None
    perms = ""
    TOKEN_FILE = flickr.tokenFile

    def __init__( self ):
        self.token = self.getCachedToken()
        self.abandonUploads = False
        self.uploaded = {}

    def authenticate( self ):
        """
        Authenticate user so we can upload images
        """
        #print "Getting new Token"
        self.getFrob()
        self.getAuthKey()
        self.getToken()
        self.cacheToken()

    def getFrob( self ):
        """
        flickr.auth.getFrob

        Returns a frob to be used during authentication. This method call must be
        signed.

        This method does not require authentication.
        Arguments

        api.key (Required)
        Your API application key. See here for more details.
        """
        d = {
            api.method  : "flickr.auth.getFrob"
            }
        url = urlGen(api.rest, d)
        try:
            response = getResponse(url)
            if isGood(response):
                FLICKR[ api.frob ] = str(response.frob.text)
            else:
                reportError(response)
        except:
            print "Error getting frob:" , str( sys.exc_info() )
            logging.error(sys.exc_info())

    def getAuthKey( self ):
        """
        Checks to see if the user has authenticated this application
        """
        d =  {
            api.frob : FLICKR[ api.frob ],
            api.perms : "delete"
            }
        url = urlGen(api.auth, d)
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

    def getToken( self ):
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
        d = {
            api.method : "flickr.auth.getToken",
            api.frob : str(FLICKR[ api.frob ])
        }
        url = urlGen(api.rest, d)
        try:
            res = getResponse(url)
            if isGood(res):
                self.token = str(res.auth.token.text)
                self.perms = str(res.auth.perms.text)
                self.cacheToken()
            else :
                reportError(res)
        except:
            print str( sys.exc_info() )
            logging.error(sys.exc_info())

    def getCachedToken( self ):
        """
        Attempts to get the flickr token from disk.
        """
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

    def checkToken( self ):
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
        if ( self.token == None ):
            return False
        d = {
            api.token  :  str(self.token) ,
            api.method :  "flickr.auth.checkToken"
        }
        url = urlGen(api.rest, d)
        try:
            res = getResponse(url)
            if isGood(res):
                self.token = str(res.auth.token.text)
                self.perms = str(res.auth.perms.text)
                return True
            else :
                reportError(res)
        except:
            print str( sys.exc_info() )
            logging.error(sys.exc_info())
        return False


    def upload( self, newImages ):
        """
        A generator to upload all of the files in newImages, and
        return the uploaded files one-by-one.
        """
        self.uploaded = shelve.open( HISTORY_FILE )
        for image in newImages:
            up = self.uploadImage( image )
            if up:
                yield up
            if self.abandonUploads:
                # the idea here is ctrl-c in the middle will still create sets
                break
        self.uploaded.close()

    def uploadImage( self, image ):
        """
        Upload a single image. Returns the photoid, or None on failure.
        """
        folderTag = image[len(IMAGE_DIR):]

        if self.uploaded.has_key(folderTag):
            stats=os.stat(image)
            logging.debug('The file %s already exists: mtime=%d, size=%d',
                         image, stats.st_mtime, stats.st_size)
            data=self.uploaded[folderTag]
            if not isinstance(data, tuple):
                logging.error('Should not have non-tuple data but continuing in any case')
                self.uploaded[folderTag] = (data, stats.st_mtime, stats.st_size)
                return None
            else:
                photo_id=data[0]
                mtime=data[1]
                filesize=data[2]
                if mtime != stats.st_mtime or filesize != stats.st_size:
                    logging.info('File has changed since previous time')
                    logging.info('Removing %s from Flickr before updating', data[0])
                    photo=flickr.Photo(data[0])
                    try:
                        photo.delete()
                        del self.uploaded[folderTag]
                        del self.uploaded[photo_id]
                    except flickr.FlickrError:
                        logging.info('File does not exist, adding')
                else:
                    return None

        try:
            logging.debug("Getting EXIF for %s", image)
            f = open(image, 'rb')
            try:
                exiftags = exifread.process_file(f)
            except MemoryError:
                exiftags = {}
            f.close()
            #print exiftags[XPKEYWORDS]
            #print folderTag
            # make one tag equal to original file path with spaces replaced by
            # # and start it with # (for easier recognition) since space is
            # used as TAG separator by flickr

            # this is needed for later syncing flickr with folders
            # look for / \ _ . and replace them with SPACE to make real Tags
            realTags = re.sub(r'[/\\_.]', ' ',
                          os.path.dirname(folderTag)).strip()

            if configdict.get('full_folder_tags', 'false').startswith('true'):
                realTags = os.path.dirname(folderTag).split(os.sep)
                realTags = (' '.join('"' + item + '"' for item in  realTags))

            picTags = '"#' + folderTag + '" ' + realTags

            #check if we need to override photo dates
            if configdict.get('override_dates', '0') == '1':
                dateTaken = datePosted = ''
                dateTakenGranularity = configdict.get('date_taken_granularity', '0')
                #fixed take date
                if configdict.get('date_taken_type', '0') == '2':
                    datePosted = configdict.get('date_posted_fixed', '')
                #fixed post date
                if configdict.get('date_posted_type', '0') == '2':
                    datePosted = configdict.get('date_posted_fixed', '')
                    #Use year and month from config ini, then calculate end of month (note: Flickr does not accept future dates. You'll get current date maximum)
                    if configdict.get('date_posted_granularity', '0') == '4':
                        datePostedY = int(datetime.fromtimestamp(datePosted).strftime("%Y"))
                        datePostedM = int(datetime.fromtimestamp(datePosted).strftime("%m"))
                        datePostedD = calendar.monthrange(datePostedY, datePostedM)[1]
                        datePosted = int((datetime(datePostedY, datePostedM, datePostedD, 23, 59, 59) - datetime(1970, 1, 1)).total_seconds())
                    #Use year from config ini, then calculate end of year (note: Flickr does not accept future dates. You'll get current date maximum)
                    if configdict.get('date_posted_granularity', '0') == '6':
                        datePostedY = int(datetime.fromtimestamp(datePosted).strftime("%Y"))
                        datePosted = int((datetime(datePostedY, 12, 31, 23, 59, 59) - datetime(1970, 1, 1)).total_seconds())
                    #Convert timestamp to GMT zone
                    dateZone =  configdict.get('date_posted_utc', '0')
                    if dateZone != '0':
                        datePosted = datePosted - int(dateZone)*3600

            if exiftags == {}:
                logging.debug('NO_EXIF_HEADER for %s', image)
            else:
                if configdict.get('override_dates', '0') == '1':
                    if 'EXIF DateTimeDigitized' in exiftags:
                        dateExif = str(exiftags['EXIF DateTimeDigitized'])
                        dateExif = dateExif[0:10].replace(':', '-') + dateExif[10:]
                        dateUnix = int((datetime(int(dateExif[0:4]), int(dateExif[5:7]), int(dateExif[8:10]), int(dateExif[11:13]), int(dateExif[14:16]), int(dateExif[17:19])) - datetime(1970, 1, 1)).total_seconds())
                        if configdict.get('date_taken_type', '0') == '1':
                            dateTaken = dateExif
                        if configdict.get('date_posted_type', '0') == '1':
                            datePosted = dateUnix
                            #Use year and month from dateExif, then calculate end of month (note: Flickr does not accept future dates. You'll get current date maximum)
                            if configdict.get('date_posted_granularity', '0') == '4':
                                datePostedY = int(datetime.fromtimestamp(datePosted).strftime("%Y"))
                                datePostedM = int(datetime.fromtimestamp(datePosted).strftime("%m"))
                                datePostedD = calendar.monthrange(datePostedY, datePostedM)[1]
                                datePosted = int((datetime(datePostedY, datePostedM, datePostedD, 23, 59, 59) - datetime(1970, 1, 1)).total_seconds())
                            #Use year from dateExif, then calculate end of year (note: Flickr does not accept future dates. You'll get current date maximum)
                            if configdict.get('date_posted_granularity', '0') == '6':
                                datePostedY = int(datetime.fromtimestamp(datePosted).strftime("%Y"))
                                datePosted = int((datetime(datePostedY, 12, 31, 23, 59, 59) - datetime(1970, 1, 1)).total_seconds())
                            #Convert timestamp to GMT zone
                            dateZone =  configdict.get('date_posted_utc', '0')
                            if dateZone != '0':
                                datePosted = datePosted - int(dateZone)*3600

                # look for additional tags in EXIF to tag picture with
                if XPKEYWORDS in exiftags:
                    printable = exiftags[XPKEYWORDS].printable
                    if len(printable) > 4:
                        exifstring = exifread.make_string(eval(printable))
                        picTags += exifstring.replace(';', ' ')

            picTags = picTags.strip()
            logging.info("Uploading image %s with tags %s", image, picTags)
            photo = ('photo', image, open(image,'rb').read())


            d = {
                api.token   : str(self.token),
                api.perms   : str(self.perms),
                "tags"      : str(picTags),
                "hidden"    : str( FLICKR["hidden"] ),
                "is_public" : str( FLICKR["is_public"] ),
                "is_friend" : str( FLICKR["is_friend"] ),
                "is_family" : str( FLICKR["is_family"] )
            }
            sig = signCall(d)
            d[ api.sig ] = sig
            d[ api.key ] = FLICKR[ api.key ]
            url = buildRequest(api.upload, d, (photo,))
            res = getResponse(url)
            if isGood(res):
                logging.debug( "successful.")
                photoid = str(res.photoid.text)
                self.logUpload(photoid, folderTag, image)
                if configdict.get('override_dates', '0') == '1':
                    self.overrideDates(image, photoid, datePosted, dateTaken, dateTakenGranularity)
                return photoid
            else :
                print "problem.."
                reportError(res)
        except KeyboardInterrupt:
            logging.debug("Keyboard interrupt seen, abandon uploads")
            print "Stopping uploads..."
            self.abandonUploads = True
            return None
        except:
            logging.error(sys.exc_info())
        return None


    def logUpload( self, photoID, imageName, image_file_name ):
        """
        Records the uploaded photo in the history file
        """
        photoID = str( photoID )
        imageName = str( imageName )
        st = os.stat( image_file_name )
        file_mtime=st.st_mtime
        file_size=st.st_size
        self.uploaded[ imageName ] = (photoID, file_mtime, file_size)
        self.uploaded[ photoID ] = imageName
        self.uploaded.close()
        self.uploaded = shelve.open( HISTORY_FILE )

    def overrideDates( self, image, photoID, datePosted, dateTaken, granularity ):
        """
        Change date_posted and date_taken parameter in an uploaded photo with Flickr granularities
        0 Y-m-d H:i:s
        4 Y-m
        6 Y
        8 Circa
        """
        try:
            photoID = str( photoID )
            logging.debug("Setting date_posted: %s and date_taken: %s for %s with id %s", str( datePosted ), str( dateTaken ), image, photoID)
            d = {
                api.token   : str(self.token),
                api.method  : "flickr.photos.setDates",
                "date_posted": str( datePosted ),
                "date_taken": str( dateTaken ),
                "date_taken_granularity" : str( granularity ),
                "photo_id"  : photoID,
            }
            sig = signCall(d)
            d[ api.sig ] = sig
            d[ api.key ] = FLICKR[ api.key ]
            url = buildRequest(api.rest, d, ())
            res = getResponse(url)
            if isGood(res):
                logging.debug( "date setting successful.")
                return
            else :
                print "problem.."
                reportError(res)
        except KeyboardInterrupt:
            logging.debug("Keyboard interrupt seen, abandon uploads")
            print "Stopping uploads..."


def parseIgnore(contents):
    """
    Parse the lines in the ignore file.
    special case if it's empty, then just match everything.
    """
    result = []
    for line in contents:
        result.append(line.strip())
    return result

def ignoreMatch(name, patterns):
    """
    Return if name matches any of the ignore patterns.
    """
    for pat in patterns:
        if glob.fnmatch.fnmatch(name, pat):
            return True
    return False

def grabNewImages(dirname):
    """
    get all images in folders and subfolders which match extensions below
    """
    images = []
    for dirpath, dirnames, filenames in os.walk(dirname, topdown=True, followlinks=True):
        ignore = '.f2fignore' in filenames
        # use os.stat here
        ignoreglobs = []
        if ignore:
            fp = open(os.path.normpath(os.path.join(dirpath, '.f2fignore')))
            ignoreglobs = parseIgnore(fp.readlines())
            fp.close()
        dirnames[:] = [d for d in dirnames if not d[0] == '.'
                       and not ignoreMatch(d, ignoreglobs)]
        for f in filenames:
            if f.startswith('.'):
                continue
            ext = f.lower().split(".")[-1]
            if ext in ALLOWED_EXT and not ignoreMatch(f, ignoreglobs):
                images.append(os.path.normpath(os.path.join(dirpath, f)))
    images.sort()
    return images

def main():
    """
    Initial entry point for the uploads
    """
    logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(levelname)s %(filename)s:%(lineno)s - %(funcName)20s() %(message)s',
                filename='debug.log',
                filemode='w')
    logging.debug('Started')
    errors = logging.FileHandler('error.log')
    errors.setLevel(logging.ERROR)
    logging.getLogger('').addHandler(errors)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter('%(asctime)s %(filename)s:%(lineno)s - %(funcName)20s() %(message)s'))
    logging.getLogger('').addHandler(console)

    uploadinstance = Uploadr()
    if not uploadinstance.checkToken():
        uploadinstance.authenticate()

    logging.info('Finding new photos from folder %s' % IMAGE_DIR)
    images = grabNewImages(IMAGE_DIR)
    logging.info('Found %d images' % len(images))
    
    # Convert history file to new format, if necessary.
    logging.info('Converting existing history file to new format, if needed')
    convert_format(images, IMAGE_DIR, HISTORY_FILE)
    logging.info('Conversion complete')

    #uploads all images that are in folders and not in history file
    logging.debug("Uploading %d images", len(images))
    uploadedNow = []
    for key, group in groupby(images, key=lambda x:dirname(x)):
        for uploaded in uploadinstance.upload(group):
            uploadedNow.append(uploaded)
        if len(uploadedNow) > 0:
            uploadinstance.uploaded.close()
            tags2set.createSets(uploadedNow, HISTORY_FILE)
            uploadedNow = []
            uploadinstance.uploaded = shelve.open( HISTORY_FILE )
        if uploadinstance.abandonUploads==True:
            break

if __name__ == "__main__":
    main()
