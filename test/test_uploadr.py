"""
Test case for uploadr.py
"""
import logging
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import unittest
import tempfile

class UploadrTest(unittest.TestCase):
    """
    Test suite for uploadr.py
    """
    def setUp(self):
        inifile = open('uploadr.ini', 'w')
        sample = open('uploadr.ini.sample', 'r')
        inifile.write(sample.read())
        inifile.close()

    def tearDown(self):
        os.unlink('uploadr.ini')

    def createDirs(self):
        tempdir = tempfile.mkdtemp()
        os.mkdir(os.path.join(tempdir, 'holidays'))
        os.mkdir(os.path.join(tempdir, 'holidays', 'family'))
        os.mkdir(os.path.join(tempdir, 'secret'))
        os.mkdir(os.path.join(tempdir, 'secret', 'documents'))
        for i in range(1, 4):
            tmpfile = open(os.path.join(tempdir, 'holidays', 'family', 'img%d.jpg'%i), 'w')
            tmpfile.close()
        tmpfile = open(os.path.join(tempdir, 'secret', 'img1.jpg'), 'w')
        tmpfile.close()
        for i in range(1, 4):
            tmpfile = open(os.path.join(tempdir, 'secret', 'documents', 'img%d.jpg'%i), 'w')
            tmpfile.close()
        return tempdir

    def testFindFilesEmpty(self):
        """
        Check find files when .f2fignore is empty does nothing
        """
        import f2flickr.uploadr
        tempdir = self.createDirs()
        tmpfile = open(os.path.join(tempdir, 'secret', '.f2fignore'), 'w')
        tmpfile.close()
        images = sorted(f2flickr.uploadr.grabNewImages(tempdir))
        self.assertEquals(7, len(images))

    def testFindFilesStar(self):
        """
        Check find files when .f2fignore has a single *
        """
        import f2flickr.uploadr
        tempdir = self.createDirs()
        tmpfile = open(os.path.join(tempdir, 'secret', '.f2fignore'), 'w')
        tmpfile.write('*\n')
        tmpfile.close()
        images = sorted(f2flickr.uploadr.grabNewImages(tempdir))
        self.assertEquals(3, len(images))

    def testFindFilesIgnore2(self):
        """
        Check find files
        """
        import f2flickr.uploadr
        tempdir = tempfile.mkdtemp()
        os.mkdir(os.path.join(tempdir, 'holidays'))
        for i in range(1, 4):
            tmpfile = open(os.path.join(tempdir, 'holidays', 'img%d.jpg'%i), 'w')
            tmpfile.close()
        tmpfile = open(os.path.join(tempdir, 'holidays', 'big.avi'), 'w')
        tmpfile.close()
        tmpfile = open(os.path.join(tempdir, 'holidays', '.f2fignore'), 'w')
        tmpfile.write("big.avi\n")
        tmpfile.close()
        images = sorted(f2flickr.uploadr.grabNewImages(tempdir))
        self.assertEquals(3, len(images))

    def testFindFilesIgnore3(self):
        """
        Check find files
        """
        import f2flickr.uploadr
        tempdir = tempfile.mkdtemp()
        os.mkdir(os.path.join(tempdir, 'holidays'))
        for i in range(1, 4):
            tmpfile = open(os.path.join(tempdir, 'holidays', 'img%d.jpg'%i), 'w')
            tmpfile.close()
        tmpfile = open(os.path.join(tempdir, 'holidays', 'big.avi'), 'w')
        tmpfile.close()
        tmpfile = open(os.path.join(tempdir, 'holidays', 'big2.avi'), 'w')
        tmpfile.close()
        tmpfile = open(os.path.join(tempdir, 'holidays', '.f2fignore'), 'w')
        tmpfile.write("*.avi\n")
        tmpfile.close()
        images = sorted(f2flickr.uploadr.grabNewImages(tempdir))
        self.assertEquals(3, len(images))

    def testFindFilesIgnoreHidden(self):
        """
        Check find files
        """
        import f2flickr.uploadr
        tempdir = tempfile.mkdtemp()
        os.mkdir(os.path.join(tempdir, 'contains_dots'))
        for i in range(1, 4):
            tmpfile = open(os.path.join(tempdir, 'contains_dots', 'img%d.jpg'%i), 'w')
            tmpfile.close()
        tmpfile = open(os.path.join(tempdir, 'contains_dots', '.big.avi'), 'w')
        tmpfile.close()
        images = sorted(f2flickr.uploadr.grabNewImages(tempdir))
        self.assertEquals(3, len(images))

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(levelname)s %(message)s',
                filename='debug.log',
                filemode='w')
    logging.debug('Started')
    unittest.main()
