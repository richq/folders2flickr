from distutils.core import setup, Command

class PyTest(Command):
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        import sys, subprocess
        errno = subprocess.call([sys.executable, 'runtests.py'])
        raise SystemExit(errno)

setup(name='folders2flickr',
      description="Uploads photos and videos to flickr.com",
      url="https://github.com/richq/folders2flickr",
      version="1.0.2",
      scripts=['folders2flickr'],
      data_files=[('share/folders2flickr', ['uploadr.ini.sample'])],
      license="GNU GPL v3",
      packages=['f2flickr'],
      install_requires=['ExifRead>=1.1.0'],
      author="Richard Quirk",
      download_url="https://github.com/richq/folders2flickr",
      cmdclass = {'test': PyTest},
      author_email="richard@quirk.es")
