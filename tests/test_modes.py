import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from src.layout import FolderTemplate
from src.metadata import Metadata, MetadataExtractor
from src.process import FileProcessor

WHEN = datetime(2015, 3, 1, 10)


class FolderTemplateTest(unittest.TestCase):
    def test_default(self):
        self.assertEqual(FolderTemplate().render(WHEN, "stylus1"), os.path.join("2015-03-01", "stylus1"))

    def test_fields(self):
        template = FolderTemplate("{year}/{month}/{day}/{camera}")
        self.assertEqual(template.render(WHEN, "x"), os.path.join("2015", "03", "01", "x"))

    def test_missing_camera_drops_empty_parts(self):
        self.assertEqual(FolderTemplate().render(WHEN, None), "2015-03-01")
        self.assertEqual(FolderTemplate("{camera}/{year}").render(WHEN, None), "2015")

    def test_empty_template_is_the_root(self):
        self.assertEqual(FolderTemplate("").render(WHEN, "x"), "")

    def test_cannot_escape_the_destination(self):
        self.assertEqual(FolderTemplate("../../{year}").render(WHEN, None), "2015")

    def test_unknown_field_is_rejected(self):
        with self.assertRaises(ValueError):
            FolderTemplate("{city}/{date}")
        with self.assertRaises(ValueError):
            FolderTemplate("{date:%Y}")


class ModesTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = os.path.realpath(tmp.name)
        self.src = os.path.join(self.root, "src")
        self.dest = os.path.join(self.root, "dest") + os.path.sep
        os.makedirs(self.src)

    def processor(self, **kwargs):
        extractor = Mock(spec=MetadataExtractor)
        extractor.read.return_value = Metadata(WHEN, "cam")
        processor = FileProcessor(extractor=extractor, **kwargs)
        processor.progress_bar_reading = processor.progress_bar_directories = processor.progress_bar_files = Mock()
        return processor

    def write(self, name, content=b"x", sub=""):
        path = os.path.join(self.src, sub, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)
        return path

    def outputs(self):
        return sorted(os.path.relpath(os.path.join(d, f), self.dest)
                      for d, _, files in os.walk(self.dest) for f in files) if os.path.isdir(self.dest) else []

    def test_dry_run_writes_nothing_but_reports_conflicts(self):
        files = [self.write("A.jpg", b"1", "a"), self.write("a.jpg", b"2", "b"), self.write("z.jpg", b"1", "c")]
        report = self.processor(dry_run=True).process(files, self.dest)
        self.assertFalse(os.path.exists(self.dest))
        self.assertTrue(all(os.path.exists(f) for f in files))
        self.assertEqual(report.written, 3)
        self.assertEqual(len(report.renamed), 1)
        self.assertTrue(report.dry_run)

    def test_move_removes_the_source_after_copying(self):
        file = self.write("a.jpg", b"data")
        report = self.processor(move=True).process([file], self.dest)
        self.assertFalse(os.path.exists(file))
        self.assertEqual(self.outputs(), [os.path.join("2015-03-01", "cam", "a.jpg")])
        self.assertEqual(report.copied, 1)

    def test_move_keeps_the_source_of_a_duplicate(self):
        first, second = self.write("a.jpg", b"same", "a"), self.write("A.JPG", b"same", "b")
        report = self.processor(move=True).process([first, second], self.dest)
        self.assertEqual(len(report.duplicates), 1)
        self.assertEqual(sum(os.path.exists(f) for f in (first, second)), 1)

    def test_move_keeps_the_source_if_verification_fails(self):
        file = self.write("a.jpg", b"data")
        processor = self.processor(move=True)
        with patch.object(processor, "_same_content", return_value=False):
            report = processor.process([file], self.dest)
        self.assertTrue(os.path.exists(file))
        self.assertEqual(self.outputs(), [])
        self.assertEqual(len(report.failed), 1)

    def test_move_keeps_the_copy_if_the_source_cannot_be_removed(self):
        file = self.write("a.jpg", b"data")
        processor = self.processor(move=True)
        with patch.object(processor, "_remove_source", side_effect=PermissionError("denied")):
            report = processor.process([file], self.dest)
        self.assertEqual(len(self.outputs()), 1)
        self.assertEqual(report.failed, [(file, "denied")])

    def test_skip_duplicates_detects_same_content_with_different_names(self):
        files = [self.write("one.jpg", b"same"), self.write("two.jpg", b"same"), self.write("three.jpg", b"other")]
        report = self.processor(skip_duplicates=True).process(files, self.dest)
        self.assertEqual(len(report.duplicates), 1)
        self.assertEqual(len(self.outputs()), 2)

    def test_without_the_flag_same_content_with_different_names_is_kept(self):
        files = [self.write("one.jpg", b"same"), self.write("two.jpg", b"same")]
        report = self.processor().process(files, self.dest)
        self.assertEqual(report.duplicates, [])
        self.assertEqual(len(self.outputs()), 2)

    def test_custom_template(self):
        file = self.write("a.jpg")
        self.processor(template=FolderTemplate("{year}/{month}")).process([file], self.dest)
        self.assertEqual(self.outputs(), [os.path.join("2015", "03", "a.jpg")])

    def test_empty_template_puts_files_in_the_destination(self):
        file = self.write("a.jpg")
        self.processor(template=FolderTemplate("")).process([file], self.dest)
        self.assertEqual(self.outputs(), ["a.jpg"])


if __name__ == "__main__":
    unittest.main()
