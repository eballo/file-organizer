import os
import tempfile
import unittest
from unittest.mock import Mock

from src.organizer import FileOrganizer
from src.process import FileProcessor


class ConflictTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = os.path.realpath(self._tmp.name)
        self.src = os.path.join(self.root, "src")
        self.dest = os.path.join(self.root, "dest") + os.path.sep
        os.makedirs(self.src)
        self.processor = FileProcessor()
        self.processor.progress_bar_reading = Mock()
        self.processor.progress_bar_directories = Mock()
        self.processor.progress_bar_files = Mock()

    def _write(self, *parts, content=b"x"):
        path = os.path.join(self.src, *parts)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)
        return path

    def _outputs(self):
        return sorted(
            os.path.relpath(os.path.join(d, f), self.dest)
            for d, _, files in os.walk(self.dest)
            for f in files
        )

    def _run(self, files):
        report = self.processor.process(files, self.dest)
        return report, [os.path.basename(p) for p in self._outputs()]

    def test_output_names_are_lowercase(self):
        report, names = self._run([self._write("IMG_0001.JPG", content=b"a")])
        self.assertEqual(names, ["img_0001.jpg"])
        self.assertEqual(report.copied, 1)

    def test_same_name_different_case_and_content_is_renamed(self):
        files = [self._write("a", "IMG.JPG", content=b"one"), self._write("b", "img.jpg", content=b"two")]
        report, names = self._run(files)
        self.assertEqual(sorted(names), ["img.jpg", "img_1.jpg"])
        self.assertEqual(len(report.renamed), 1)
        self.assertEqual(report.failed, [])

    def test_identical_files_are_reported_as_duplicates(self):
        files = [self._write("a", "IMG.JPG", content=b"same"), self._write("b", "img.jpg", content=b"same")]
        report, names = self._run(files)
        self.assertEqual(names, ["img.jpg"])
        self.assertEqual(len(report.duplicates), 1)

    def test_existing_destination_file_is_not_overwritten(self):
        first = self._write("a", "img.jpg", content=b"one")
        self._run([first])
        other = self._write("b", "IMG.JPG", content=b"two")
        report, names = self._run([other])
        self.assertEqual(sorted(names), ["img.jpg", "img_1.jpg"])
        self.assertEqual(len(report.renamed), 1)

    def test_rerun_is_idempotent(self):
        files = [self._write("img.jpg", content=b"one")]
        self._run(files)
        report, names = self._run(files)
        self.assertEqual(names, ["img.jpg"])
        self.assertEqual(len(report.duplicates), 1)

    def test_unreadable_file_is_reported_and_others_continue(self):
        good = self._write("good.jpg", content=b"ok")
        missing = os.path.join(self.src, "missing.jpg")
        report, names = self._run([good, missing])
        self.assertEqual(names, ["good.jpg"])
        self.assertEqual([f[0] for f in report.failed], [missing])

    def test_clean_name_removes_unsafe_characters(self):
        self.assertEqual(FileProcessor._clean_name("Canon/EOS 60D\x00"), "canoneos60d")
        self.assertEqual(FileProcessor._clean_name(b"NIKON D5"), "nikond5")
        self.assertIsNone(FileProcessor._clean_name("///"))
        self.assertIsNone(FileProcessor._clean_name(42))

    def test_files_inside_destination_are_ignored(self):
        self._write("a.jpg")
        dest_inside = os.path.join(self.src, "out")
        os.makedirs(dest_inside)
        with open(os.path.join(dest_inside, "b.jpg"), "wb") as f:
            f.write(b"x")
        organizer = FileOrganizer(self.src, dest_inside, (".jpg",))
        organizer.validate_data_input()
        all_files, processed = organizer._filter_files(organizer.source, (".jpg",))
        self.assertEqual([os.path.basename(p) for p in processed], ["a.jpg"])


if __name__ == "__main__":
    unittest.main()
