import sys
sys.path.append('..')
import f2flickr.flickr as flickr

_flickr_test_login = flickr.test_login
_flickr_Photo = flickr.Photo

class FakePhoto(object):

    def __init__(self, id):
        self.id = id

class FakeUser(object):
    def __init__(self):
        self.id = 1
        self._photosets = []

    def getPhotosets(self):
        return [s for s in self._photosets]

    def addPhotosetInternal(self, ps):
        self._photosets.append(ps)

    def clearPhotosetsInternal(self):
        self._photosets = []

thefakeuser = FakeUser()
def fakelogin():
    return thefakeuser

class FakePhotoset(object):
    counter = 0

    def __init__(self, id, title, primary, photos=0, description='', \
                 secret='', server=''):
        self.__id = id
        self.title = title
        self.__primary = primary
        self.__description = description
        self.__count = photos
        self.__secret = secret
        self.__server = server
        self.__photos = []

    def getPhotos(self):
        return self.__photos

    def editPhotos(self, photos, primary=None):
        newphotos = [photo.id for photo in photos if photo.id not in self.__photos]
        self.__photos.extend(newphotos)
        if self.__primary.id not in self.__photos:
            self.__photos.append(self.__primary.id)

    def create(cls, photo, title, description=''):
        ps = FakePhotoset(FakePhotoset.counter,
                         title, photo, description)
        FakePhotoset.counter = FakePhotoset.counter + 1
        thefakeuser.addPhotosetInternal(ps)
        return ps

    create = classmethod(create)

flickr.test_login = fakelogin
flickr.Photo = FakePhoto
flickr.Photoset = FakePhotoset
