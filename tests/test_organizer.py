import os
import unittest

from src.constants import DEFAULT_EXTENSION
from src.organizer import FileOrganizer


class FileOrganizerTest(unittest.TestCase):

    def setUp(self):
        simp_path = 'tests/fixtures/test/'
        self.source = os.path.abspath(simp_path)
        self.extensions = DEFAULT_EXTENSION
        self.organizer = FileOrganizer(self.source, None, self.extensions)

    def test_get_all_files(self):
        all_files = self.organizer.get_all_files(self.source)
        assert len(all_files) == 3

    def test_get_list_of_files(self):
        all_files = self.organizer.get_list_of_files_to_be_processed(self.source, self.extensions)
        assert len(all_files) == 1
