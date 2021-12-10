import glob
import os
from typing import Tuple, List, Union, Any, Set

from src.constants import DEFAULT_EXTENSION
from src.process import FileProcessor
import logging

from src.utils import do_you_want_to_continue


class FileOrganizer:
    def __init__(
        self, source: str, destination: str, extensions: Tuple[Union[str, Any], ...]
    ):
        self.file_process = FileProcessor()
        self.source = source
        self.destination = destination
        self.extensions = extensions if extensions else DEFAULT_EXTENSION

    @staticmethod
    def get_all_files(
        source: str,
    ) -> List[str]:
        matches = []
        for filename in glob.iglob(source + "**" + os.path.sep + "*.*", recursive=True):
            matches.append(filename.lower())
        return matches

    @staticmethod
    def get_list_of_files_to_be_processed(
        source: str, extensions: Tuple[str]
    ) -> List[str]:
        matches = []
        for filename in glob.iglob(source + "**" + os.path.sep + "*.*", recursive=True):
            base, ext = os.path.splitext(filename)
            if ext.lower() in extensions:
                matches.append(filename.lower())
        return matches

    @staticmethod
    def get_list_missing_files(
        all_files: List[str], processed_files: List[str]
    ) -> List[str]:
        return [x for x in all_files if x not in processed_files]

    @staticmethod
    def get_unique_extensions(files: List[str]) -> Set[str]:
        unique_extensions = set()
        for file in files:
            extension = os.path.splitext(file)[1]
            if extension not in unique_extensions:
                unique_extensions.add(extension)
        return unique_extensions

    def start(self):
        if self.source and self.destination:
            logging.info("[+] Start Processing")
            all_files = self.get_all_files(self.source)
            list_of_files_to_be_processed = self.get_list_of_files_to_be_processed(
                self.source, self.extensions
            )
            missing = self.get_list_missing_files(
                all_files, list_of_files_to_be_processed
            )

            if list_of_files_to_be_processed:
                self.reporting_summary(
                    all_files, list_of_files_to_be_processed, missing
                )
                do_you_want_to_continue()
                self.file_process.process(
                    list_of_files_to_be_processed, self.destination
                )

            else:
                logging.info("[-] No files found that matches the types")

    def reporting_summary(self, all_files, list_of_processed, missing):
        logging.info(" ")
        logging.info("------------------------")
        logging.info("  Files Report  ")
        logging.info("------------------------")
        logging.info(" Extensions to be processed : %s ", self.extensions)
        logging.info(" Files found : %s / %s ", len(list_of_processed), len(all_files))
        logging.info(" ")
        logging.info(" Missing files   : %s / %s", len(missing), len(all_files))
        logging.info(
            " Missed files have the following extensions: %s",
            self.get_unique_extensions(missing),
        )
        logging.info(" ")
