import os
import unittest
from unittest.mock import patch

from src.constants import DEFAULT_EXTENSION
from src.organizer import FileOrganizer


class FileOrganizerTest(unittest.TestCase):

    def setUp(self):
        simp_path = 'tests/fixtures/test/'
        self.source = os.path.abspath(simp_path)
        self.destination = os.path.abspath('tests/fixtures/destination/')
        self.extensions = DEFAULT_EXTENSION
        self.organizer = FileOrganizer(self.source, self.destination, self.extensions)

    def test_validate_data_input(self):
        simp_path = 'tests/fixtures/test'
        source = os.path.abspath(simp_path)
        destination = os.path.abspath('tests/fixtures/destination')
        organizer = FileOrganizer(source, destination, DEFAULT_EXTENSION)

        organizer.validate_data_input()

        assert organizer.source == os.path.abspath("tests/fixtures/test") + os.path.sep
        assert organizer.destination == os.path.abspath("tests/fixtures/destination/") + os.path.sep

    @patch('src.organizer.glob.iglob')
    def test_get_files_local(self, mock_iglob):
        mock_iglob.return_value = [
            os.path.join(self.source, 'file1.txt'),
            os.path.join(self.source, 'file2.mp3'),
            os.path.join(self.source, 'file3.jpg')
        ]

        files = self.organizer.get_files(self.source, self.extensions)

        self.assertEqual(len(files[0]), 3)  # all files
        self.assertEqual(len(files[1]), 1)  # processed files
        self.assertEqual(len(files[2]), 2)  # missing files

    @patch('src.organizer.glob.iglob')
    def test_filter_files(self, mock_iglob):
        mock_iglob.return_value = [
            os.path.join(self.source, 'file1.txt'),
            os.path.join(self.source, 'file2.mp3'),
            os.path.join(self.source, 'file3.jpg')
        ]

        all_files, processed_files = self.organizer._filter_files(self.source, self.extensions)

        self.assertEqual(len(all_files), 3)  # all files
        self.assertEqual(len(processed_files), 1)  # processed files

    def test_get_unique_extensions(self):
        files = [
            'test1.txt', 'test2.mp3', 'test3.docx', 'test4.txt'
        ]
        unique_extensions = self.organizer.get_unique_extensions(files)

        self.assertEqual(len(unique_extensions), 3)
        self.assertIn('.txt', unique_extensions)
        self.assertIn('.mp3', unique_extensions)
        self.assertIn('.docx', unique_extensions)

    @patch('src.organizer.FileProcessor.process')
    @patch('src.organizer.do_you_want_to_continue')
    @patch('src.organizer.FileOrganizer.get_files')
    def test_start_with_files(self, mock_get_files, mock_do_you_want_to_continue, mock_process):
        mock_get_files.return_value = (
            ['file1.txt', 'file2.mp3', 'file3.docx'],
            ['file1.txt'],
            ['file2.mp3', 'file3.docx']
        )
        mock_do_you_want_to_continue.return_value = True

        self.organizer.start()

        mock_get_files.assert_called_once()
        mock_process.assert_called_once_with(['file1.txt'], self.destination + os.path.sep)
        mock_do_you_want_to_continue.assert_called_once()

    @patch('src.organizer.FileOrganizer.get_files')
    @patch('src.organizer.logging.info')
    def test_start_with_no_files(self, mock_logging_info, mock_get_files):
        mock_get_files.return_value = ([], [], [])

        self.organizer.start()

        mock_get_files.assert_called_once()
        mock_logging_info.assert_called_with("[-] No files found that matches the types")

    @patch('src.organizer.logging.info')
    def test_reporting_summary(self, mock_logging_info):
        all_files = ['file1.txt', 'file2.mp3', 'file3.jpeg']
        processed_files = ['file1.jpeg']
        missing_files = ['file2.mp3', 'file3.docx']

        self.organizer.reporting_summary(all_files, processed_files, missing_files)

        self.assertEqual(mock_logging_info.call_count, 10)
        calls = [
            unittest.mock.call(" "),
            unittest.mock.call("------------------------"),
            unittest.mock.call("  Files Report  "),
            unittest.mock.call("------------------------"),
            unittest.mock.call(" Extensions to be processed : %s ", self.extensions),
            unittest.mock.call(" Files found : %s / %s ", len(processed_files), len(all_files)),
            unittest.mock.call(" Missing files   : %s / %s", len(missing_files), len(all_files)),
            unittest.mock.call(" Missed files have the following extensions: %s", {'.mp3', '.docx'}),
            unittest.mock.call(" ")
        ]
        mock_logging_info.assert_has_calls(calls, any_order=True)

