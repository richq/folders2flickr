from distutils.core import setup

setup(name='folders2flickr',
      description="Uploads photos and videos to flickr.com",
      url="https://github.com/richq/folders2flickr",
      version="1.0",
      scripts=['folders2flickr'],
      data_files=[('share/folders2flickr', ['uploadr.ini.sample'])],
      license="GNU GPL v3",
      packages=['f2flickr'],
      author="Richard Quirk",
      download_url="https://github.com/richq/folders2flickr",
      author_email="richard@quirk.es")
