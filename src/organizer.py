import glob
import os
from typing import Tuple, List, Union, Any

from src.constants import DEFAULT_EXTENSION
from src.process import FileProcessor


class FileOrganizer:

    def __init__(self, source: str, destination: str, extensions: Tuple[Union[str, Any], ...]):
        self.file_process = FileProcessor()
        self.source = source
        self.destination = destination
        self.extensions = extensions if extensions else DEFAULT_EXTENSION

    @staticmethod
    def get_all_files(source: str, ) -> List[str]:
        matches = []
        for filename in glob.iglob(source + '**' + os.path.sep + '*.*', recursive=True):
            matches.append(filename.lower())
        return matches

    @staticmethod
    def get_list_of_files_to_be_processed(source: str, extensions: Tuple[str]) -> List[str]:
        matches = []
        for filename in glob.iglob(source + '**' + os.path.sep + '*.*', recursive=True):
            base, ext = os.path.splitext(filename)
            if ext.lower() in extensions:
                matches.append(filename.lower())
        return matches

    @staticmethod
    def get_list_missing_files(all_files:List[str], processed_files: List[str]) -> List[str]:
        return [x for x in all_files if x not in processed_files]

    def start(self):
        if self.source and self.destination:
            print("[+] Start Processing")
            all_files = self.get_all_files(self.source)
            list_of_files_to_be_processed = self.get_list_of_files_to_be_processed(self.source, self.extensions)
            missing = self.get_list_missing_files(all_files, list_of_files_to_be_processed)
            if list_of_files_to_be_processed:
                self.file_process.process(list_of_files_to_be_processed, self.destination)
                self.reporting_summary(all_files, list_of_files_to_be_processed, missing)
            else:
                print(f"[-] No files found that matches the types")

    @staticmethod
    def reporting_summary(all_files, list_of_processed, missing):
        print(" ")
        print("------------------------")
        print("  Summary Files Report  ")
        print("------------------------")
        print(f" Processed files : {len(list_of_processed)}/{len(all_files)}")
        print(f" Missing files   : {len(missing)}/{len(all_files)}")
        print(" ")
        print(" Missed files:")
        print(" ")
        for file in missing:
            print(file)
