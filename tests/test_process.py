import os
import unittest
from unittest.mock import patch, Mock

from datetime import datetime

from src.metadata import Metadata
from src.process import FileProcessor


class ProcessTest(unittest.TestCase):
    def setUp(self):
        self.processor = FileProcessor()
        self.image_list = [
            os.path.abspath(
                "tests/fixtures/test/església st pere de rubí 150301_2014.jpg"
            )
        ]
        self.destination = os.path.abspath("tests/fixtures/output/")

    @patch("os.path.isdir")
    @patch("os.makedirs")
    def test_create_destination(self, mock_mkdir, mock_isdir):
        mock_isdir.return_value = False
        self.processor.create_destination(self.destination)
        mock_mkdir.assert_called_once_with(self.destination)

    @patch("os.path.isdir")
    def test_create_destination_exists(self, mock_isdir):
        mock_isdir.return_value = True
        with patch("os.makedirs") as mock_mkdir:
            self.processor.create_destination(self.destination)
            mock_mkdir.assert_not_called()

    def test_folder_uses_capture_date_and_camera(self):
        with patch.object(self.processor, "_read_metadata", return_value=Metadata(datetime(2020, 5, 17, 23, 59), "canon60d")):
            self.assertEqual(self.processor.folder_for("image.jpg"), os.path.join("2020-05-17", "canon60d"))

    def test_folder_without_camera_is_just_the_date(self):
        with patch.object(self.processor, "_read_metadata", return_value=Metadata(datetime(2020, 5, 17), None)):
            self.assertEqual(self.processor.folder_for("image.jpg"), "2020-05-17")

    def test_capture_info_falls_back_to_mtime(self):
        with patch.object(self.processor, "_read_metadata", return_value=Metadata()):
            with patch("os.path.getmtime", return_value=1609459200):
                date, camera = self.processor.capture_info("image.jpg")
        self.assertEqual(date, datetime.fromtimestamp(1609459200))
        self.assertIsNone(camera)

    def test_capture_info_is_cached(self):
        with patch.object(self.processor, "_read_metadata", return_value=Metadata(datetime(2020, 1, 2), None)) as read:
            self.processor.capture_info("a.jpg")
            self.processor.capture_info("a.jpg")
        read.assert_called_once()

    def test_process_in_parallel_reports_failures(self):
        self.processor.progress_bar_files = Mock()
        with patch.object(self.processor, "move_images", side_effect=OSError("boom")):
            report = self.processor.process_in_parallel(self.image_list, self.destination)
        self.assertEqual(report.failed, [(self.image_list[0], "boom")])
        self.assertEqual(report.copied, 0)

    @patch("src.process.FileProcessor.process_in_parallel")
    def test_process(self, mock_process_in_parallel):
        with patch("src.process.FileProcessor.get_unique_folders") as mock_get_dates:
            mock_get_dates.return_value = {"2021-01-01"}
            with patch("src.process.FileProcessor.create_directories") as mock_create_dirs:
                with patch("src.process.FileProcessor.create_destination") as mock_create_dest:
                    self.processor.process(self.image_list, self.destination)
                    mock_create_dest.assert_called_with(self.destination)
                    mock_create_dirs.assert_called_with({"2021-01-01"}, self.destination)
                    mock_process_in_parallel.assert_called_with(self.image_list, self.destination)
