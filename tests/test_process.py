import os
import unittest
from unittest.mock import patch, PropertyMock, Mock

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
    @patch("os.mkdir")
    def test_create_destination(self, mock_mkdir, mock_isdir):
        mock_isdir.return_value = False
        self.processor.create_destination(self.destination)
        mock_mkdir.assert_called_once_with(self.destination)

    @patch("os.path.isdir")
    def test_create_destination_exists(self, mock_isdir):
        mock_isdir.return_value = True
        with patch("os.mkdir") as mock_mkdir:
            self.processor.create_destination(self.destination)
            mock_mkdir.assert_not_called()

    @patch("src.process.FileProcessor.get_exif")
    @patch("src.process.FileProcessor.get_data")
    def test_modification_date(self, mock_get_exif, mock_get_data):
        mock_get_exif.return_value = Mock()
        mock_get_data.return_value = "Canon 60D"
        with patch("os.path.getmtime") as mock_getmtime:
            mock_getmtime.return_value = 1609459200  # Jan 1, 2021
            date, model = self.processor.modification_date("image.jpg")
            self.assertEqual(date, "2021-01-01")

    @patch("src.process.FileProcessor.process_in_parallel")
    def test_process(self, mock_process_in_parallel):
        with patch("src.process.FileProcessor.get_unique_sorted_dates") as mock_get_dates:
            mock_get_dates.return_value = {("2021-01-01", "model")}
            with patch("src.process.FileProcessor.create_directories") as mock_create_dirs:
                with patch("src.process.FileProcessor.create_destination") as mock_create_dest:
                    self.processor.process(self.image_list, self.destination)
                    mock_create_dest.assert_called_with(self.destination)
                    mock_create_dirs.assert_called_with({("2021-01-01", "model")}, self.destination)
                    mock_process_in_parallel.assert_called_with(self.image_list, self.destination)
