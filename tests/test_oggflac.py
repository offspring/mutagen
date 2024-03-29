import os
import shutil

from tempfile import mkstemp

from mutagen._compat import cBytesIO
from mutagen.oggflac import OggFLAC, OggFLACStreamInfo, delete
from mutagen.ogg import OggPage, error as OggError
from tests import TestCase
from tests.test_ogg import TOggFileTypeMixin
from tests.test_flac import have_flac, call_flac


class TOggFLAC(TestCase, TOggFileTypeMixin):
    Kind = OggFLAC

    def setUp(self):
        original = os.path.join("tests", "data", "empty.oggflac")
        fd, self.filename = mkstemp(suffix='.ogg')
        os.close(fd)
        shutil.copy(original, self.filename)
        self.audio = OggFLAC(self.filename)

    def tearDown(self):
        os.unlink(self.filename)

    def test_vendor(self):
        self.failUnless(
            self.audio.tags.vendor.startswith("reference libFLAC"))
        self.failUnlessRaises(KeyError, self.audio.tags.__getitem__, "vendor")

    def test_streaminfo_bad_marker(self):
        page = OggPage(open(self.filename, "rb")).write()
        page = page.replace(b"fLaC", b"!fLa", 1)
        self.failUnlessRaises(IOError, OggFLACStreamInfo, cBytesIO(page))

    def test_streaminfo_too_short(self):
        page = OggPage(open(self.filename, "rb")).write()
        self.failUnlessRaises(OggError, OggFLACStreamInfo, cBytesIO(page[:10]))

    def test_streaminfo_bad_version(self):
        page = OggPage(open(self.filename, "rb")).write()
        page = page.replace(b"\x01\x00", b"\x02\x00", 1)
        self.failUnlessRaises(IOError, OggFLACStreamInfo, cBytesIO(page))

    def test_flac_reference_simple_save(self):
        if not have_flac:
            return
        self.audio.save()
        self.scan_file()
        self.assertEqual(call_flac("--ogg", "-t", self.filename), 0)

    def test_flac_reference_really_big(self):
        if not have_flac:
            return
        self.test_really_big()
        self.audio.save()
        self.scan_file()
        self.assertEqual(call_flac("--ogg", "-t", self.filename), 0)

    def test_module_delete(self):
        delete(self.filename)
        self.scan_file()
        self.failIf(OggFLAC(self.filename).tags)

    def test_flac_reference_delete(self):
        if not have_flac:
            return
        self.audio.delete()
        self.scan_file()
        self.assertEqual(call_flac("--ogg", "-t", self.filename), 0)

    def test_flac_reference_medium_sized(self):
        if not have_flac:
            return
        self.audio["foobar"] = "foobar" * 1000
        self.audio.save()
        self.scan_file()
        self.assertEqual(call_flac("--ogg", "-t", self.filename), 0)

    def test_flac_reference_delete_readd(self):
        if not have_flac:
            return
        self.audio.delete()
        self.audio.tags.clear()
        self.audio["foobar"] = "foobar" * 1000
        self.audio.save()
        self.scan_file()
        self.assertEqual(call_flac("--ogg", "-t", self.filename), 0)

    def test_not_my_ogg(self):
        fn = os.path.join('tests', 'data', 'empty.ogg')
        self.failUnlessRaises(IOError, type(self.audio), fn)
        self.failUnlessRaises(IOError, self.audio.save, fn)
        self.failUnlessRaises(IOError, self.audio.delete, fn)

    def test_mime(self):
        self.failUnless("audio/x-oggflac" in self.audio.mime)
