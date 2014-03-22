[![Build Status](https://travis-ci.org/richq/folders2flickr.png)](https://travis-ci.org/richq/folders2flickr)

This is a fork of the seemingly defunct http://code.google.com/p/folders2flickr/ project.

When looking for a good way to upload photos and videos to flickr from the
command line, I found the following free software options:

* flickrfs - doesn't support video, freezes all the time
* imguploadr - has too many dependencies and after fixing the Solaris-based Makefile it still didn't work
* flickr\_upload - doesn't support sets, is in "write-only" Perl
* uploadr - really basic, hardcoded paths and just too untested

After diving into each, folders2flickr seemed the best. It is based on uploadr,
but fixes the problems I had. However it still had some bugs:

* sets didn't quite work
* slow, as it did pointless things multiple times

Fortunately it is written in Python and the code wasn't too bad. I've cleaned
it up and it runs great on GNU/Linux - specifically tested on Ubuntu 12.04.

To fix the slow initial run, it will upload all photos and videos it doesn't know about.
So keep the database it creates in a safe place!

## INSTALLATION

The easiest way is to use [pip](http://www.pip-installer.org).

    pip install --user git+https://github.com/richq/folders2flickr.git

This will create `~/.local/bin/folders2flickr` and install the library to the right place in `.local`.
The sample configuration file can be created like this:

    cp ~/.local/share/folders2flickr/uploadr.ini.sample ~/.uploadr.ini
    sensible-editor ~/.uploadr.ini
    # modify 'imagedir', etc.

If you want to use a local clone of the repository then please be aware that
folders2flickr depends on the [python-exif](https://github.com/ianare/exif-py)
package. Once you have installed that package, create a clone of folders2flickr using git:

    git clone https://github.com/richq/folders2flickr.git

Then you will need to configure the directories to use:

    cp uploadr.ini.sample uploadr.ini
    sensible-editor uploadr.ini
    # modify at least 'imagedir' to point to the location of new images

I try to keep the master branch usable, but there are point releases if you
prefer a stable fixed version. To install a release, download the zip file,
unpack it and away you go. The python-exif dependency will be included in these
zips.

## WHAT IS UPLOADED

The photos and videos in the directory given in the uploadr.ini file are
eventually uploaded to flickr and placed into sets. Only files with the
extensions jpg, gif, png, avi and mov are uploaded, and flickr may reject them
if they are not in the correct format.

If you add the file `.f2fignore` to a directory then it can be used to ignore
files and subdirectories.  Ignored files will not be uploaded, and the script
will not descend into ignored subdirectories.

The contents of the `.f2fignore` file is a series of glob patterns,
one pattern or filename per line. Subdirectories are also ignored if they
match the pattern. For example, to ignore the file `MVI_3847.AVI` you
can either specify the file exactly:

    MVI_3847.AVI

or you could add a pattern to the ignore file:

    MVI_*.AVI

The pattern is case sensitive and uses Python's [fnmatch](http://docs.python.org/2/library/fnmatch.html).

## RUNTIME DATA FILES

Two files are created during execution:

* `.flickrToken`, which has the token to authenticate to flickr
* the history file, which contains the photos uploaded so far

By default both of these are created in the current working directory, so next
time you run folders2flickr you should do so from the same place.
