import os
import unittest

from src.process import FileProcessor


class ProcessTest(unittest.TestCase):

    def setUp(self):
        self.image_list = [os.path.abspath('tests/fixtures/test/església st pere de rubí 150301_2014.jpg')]
        self.destination = os.path.abspath('tests/fixtures/output/')
        self.process = FileProcessor()

    def test_create_destination(self):
        unique_dates = self.process.get_unique_sorted_dates(self.image_list)
        assert len(unique_dates) == 1
        assert ('2015-03-01', 'stylus1') in unique_dates

