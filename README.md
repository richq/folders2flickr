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
