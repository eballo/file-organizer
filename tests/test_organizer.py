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

    def test_get_files(self):
        files = self.organizer.get_files(False, self.source, self.extensions)
        assert len(files[0]) == 3
        assert len(files[1]) == 1
