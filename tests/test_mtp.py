"""
The real MTP layer needs Windows and a phone, so these tests replace `src.mtp_windows` with an in-memory device.
They check everything around it: device selection, source path handling, metadata fallbacks and the copy.
"""

import io
import os
import sys
import tempfile
import types
import unittest
from datetime import datetime
from unittest.mock import patch

from PIL import Image

import reorganize
import src
from src.constants import DEFAULT_EXTENSION
from src.organizer import FileOrganizerWin32
from src.process import FileProcessorWin32


def jpeg_with_exif() -> bytes:
    exif = Image.Exif()
    exif[271], exif[272] = "Samsung", "Galaxy S21"
    exif[0x8769] = {36867: "2021:06:05 14:30:00"}
    out = io.BytesIO()
    Image.new("RGB", (4, 4)).save(out, "JPEG", exif=exif)
    return out.getvalue()


class FakeContent:
    def __init__(self, path, data, date):
        self.path, self.data, self.date = path, data, date

    def getName(self):
        return os.path.basename(self.path)

    def getDate(self):
        return self.date

    def read_data(self):
        return bytearray(self.data)

    def downloadStream(self, stream):
        stream.write(bytearray(self.data))


class FakeDevice:
    def __init__(self, name):
        self.name = name

    def getDescription(self):
        return self.name


def fake_mtp_module(files):
    """files: {'Phone/DCIM/a.jpg': (bytes, datetime or None)}"""
    module = types.ModuleType("src.mtp_windows")
    module.get_portable_devices = lambda: [FakeDevice("Phone")]

    def content(path):
        if path not in files:
            return None
        return FakeContent(path, *files[path])

    module.get_content_from_device_path = content

    def get_sub_files(path):
        return [p for p in files if p.startswith(path + "/")]

    module.get_sub_files = get_sub_files
    return module


def install_fake(testcase, module):
    """Makes `import src.mtp_windows` return the fake. Only that entry is touched: patch.dict would drop every
    module imported meanwhile (tqdm and multiprocessing among them)."""
    missing = object()
    old_module = sys.modules.get("src.mtp_windows", missing)
    old_attr = getattr(src, "mtp_windows", missing)
    sys.modules["src.mtp_windows"] = module
    src.mtp_windows = module

    def restore():
        for container, restore_to in ((sys.modules, old_module), (None, old_attr)):
            if container is None:
                if restore_to is missing:
                    delattr(src, "mtp_windows")
                else:
                    src.mtp_windows = restore_to
            elif restore_to is missing:
                del sys.modules["src.mtp_windows"]
            else:
                sys.modules["src.mtp_windows"] = restore_to

    testcase.addCleanup(restore)


class MtpFlowTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dest = os.path.join(os.path.realpath(tmp.name), "out")
        self.files = {
            "Phone/DCIM/IMG_1.JPG": (jpeg_with_exif(), datetime(2020, 1, 1)),
            "Phone/DCIM/noexif.jpg": (b"not an image", datetime(2019, 2, 3)),
            "Phone/DCIM/clip.mp4": (b"video", datetime(2018, 4, 5)),
            "Phone/DCIM/nodate.png": (b"not an image", None),
            "Phone/DCIM/notes.txt": (b"text", None),
        }
        install_fake(self, fake_mtp_module(self.files))
        patcher = patch("src.organizer.do_you_want_to_continue")
        patcher.start()
        self.addCleanup(patcher.stop)

    def outputs(self):
        return sorted(os.path.relpath(os.path.join(d, f), self.dest).replace(os.sep, "/")
                      for d, _, names in os.walk(self.dest) for f in names)

    def run_organizer(self, source="Phone/DCIM"):
        organizer = FileOrganizerWin32(source, self.dest, DEFAULT_EXTENSION, FileProcessorWin32())
        return organizer.start()

    def test_source_is_not_given_an_os_separator(self):
        organizer = FileOrganizerWin32("Phone/DCIM", self.dest, DEFAULT_EXTENSION)
        organizer.validate_data_input()
        self.assertEqual(organizer.source, "Phone/DCIM")
        self.assertTrue(organizer.destination.endswith(os.path.sep))

    def test_files_are_copied_with_exif_or_device_dates(self):
        report = self.run_organizer()
        self.assertEqual(report.failed, [])
        today = datetime.today().strftime("%Y-%m-%d")
        self.assertEqual(self.outputs(), sorted([
            "2021-06-05/samsung_galaxys21/img_1.jpg",  # EXIF
            "2019-02-03/noexif.jpg",                   # device date, no EXIF
            "2018-04-05/clip.mp4",                     # video: device date, not downloaded to read metadata
            f"{today}/nodate.png",                     # nothing known: today, as before
        ]))

    def test_trailing_separator_in_the_device_path_is_accepted(self):
        self.assertEqual(self.run_organizer("Phone/DCIM/").failed, [])
        self.assertEqual(len(self.outputs()), 4)

    def test_clashing_names_are_renamed_on_devices(self):
        self.files["Phone/Other/img_1.jpg"] = (jpeg_with_exif() + b"x", datetime(2021, 6, 5))
        report = self.run_organizer("Phone")
        self.assertEqual(len(report.renamed), 1)
        self.assertEqual(report.failed, [])


class DeviceSelectionTest(unittest.TestCase):
    def arguments(self, argv, windows=True, answer="0"):
        fake = fake_mtp_module({})
        fake.get_portable_devices = lambda: [FakeDevice("Tablet"), FakeDevice("Phone")]
        install_fake(self, fake)
        win_ver = ("10", "10.0", "SP0", "Multiprocessor Free") if windows else ("", "", "", "")
        with patch.object(sys, "argv", ["reorganize.py"] + argv), \
                patch("platform.win32_ver", return_value=win_ver), \
                patch("builtins.input", return_value=answer):
            return reorganize.get_arguments()

    def test_on_windows_without_source_a_device_is_chosen(self):
        options = self.arguments(["--destination", "out"], answer="1")
        self.assertTrue(options.is_mtp)
        self.assertEqual(options.source, "Phone")

    def test_invalid_device_number_exits(self):
        with self.assertRaises(SystemExit):
            self.arguments(["--destination", "out"], answer="7")

    def test_without_source_outside_windows_is_an_error(self):
        with self.assertRaises(SystemExit) as ctx:
            self.arguments(["--destination", "out"], windows=False)
        self.assertEqual(ctx.exception.code, 2)

    def test_move_is_rejected_for_devices(self):
        with self.assertRaises(SystemExit) as ctx:
            self.arguments(["--destination", "out", "--move"])
        self.assertEqual(ctx.exception.code, 2)

    def test_a_real_folder_is_not_mtp(self):
        with tempfile.TemporaryDirectory() as folder:
            options = self.arguments(["--source", folder, "--destination", "out"])
        self.assertFalse(options.is_mtp)


if __name__ == "__main__":
    unittest.main()
