import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Tuple, Set, Optional
from shutil import copyfile
from pathlib import Path
from PIL import Image, ExifTags, UnidentifiedImageError
from PIL.Image import Exif
import logging
from tqdm import tqdm


class FileProcessor:

    def __init__(self):
        self.progress_bar_reading = None
        self.progress_bar_directories = None
        self.progress_bar_files = None
        pass

    def process(self, images: List[str], destination: str):
        self.create_destination(destination)

        logging.info("[+] Reading files ")
        self.progress_bar_reading = tqdm(total=len(images), unit="files")
        sorted_dates = self.get_unique_sorted_dates(images)

        logging.info("[+] Creating directories ")
        self.progress_bar_directories = tqdm(total=len(sorted_dates), unit="directory")
        self.create_directories(sorted_dates, destination)

        logging.info("[+] Copying files ")
        self.progress_bar_files = tqdm(total=len(images), unit="file")
        self.process_in_parallel(images, destination)

    @staticmethod
    def create_destination(directory_name):
        try:
            if not os.path.isdir(directory_name):
                os.mkdir(directory_name)
            else:
                logging.info("[-] Output directory already exists")
        except OSError:
            logging.warning("Creation of the directory %s failed" % directory_name)

    def create_directories(self, sorted_dates, destination):
        for date, model in sorted_dates:
            if not os.path.isdir(destination + date):
                self.create_destination(destination + date)
            if model:
                if not os.path.isdir(destination + date + os.path.sep + model):
                    self.create_destination(destination + date + os.path.sep + model)
            self.progress_bar_directories.update()
        self.progress_bar_directories.close()

    def get_unique_sorted_dates(self, images: List[str]) -> Set[Tuple[str, str]]:
        unique_dates = set()
        for image in images:
            unique_dates.add(self.modification_date(image))
            self.progress_bar_reading.update()
        self.progress_bar_reading.close()
        return unique_dates

    def process_in_parallel(self, images: List[str], destination: str):
        args = [(image, destination) for image in images]
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(self.move_images, args)
        self.progress_bar_files.close()
        logging.info("[+] All files were moved successfully! ")

    def move_images(self, args: List[Tuple[str, str]]):
        image, destination = args
        date, model = self.modification_date(image)
        destination += date + os.path.sep
        if model:
            destination += model + os.path.sep
        copyfile(image, destination + Path(image).name)
        self.progress_bar_files.update()

    def modification_date(self, file: str) -> Tuple[str, str]:
        t = os.path.getmtime(file)
        date = datetime.fromtimestamp(t)
        date = str(date.year) + '-' + str(date.month).zfill(2) + '-' + str(date.day).zfill(2)
        model = self.get_data(self.get_exif(file), "Model")
        return date, model

    @staticmethod
    def get_exif(image: str) -> Optional[Exif]:
        exif_raw = None
        try:
            img = Image.open(image)
            exif_raw = img.getexif()
        except UnidentifiedImageError:
            pass
        return exif_raw

    @staticmethod
    def get_data(exif_raw: Optional[Exif], field: str) -> str:
        model = None
        if exif_raw:
            for tag, value in exif_raw.items():
                decoded_tag = ExifTags.TAGS.get(tag, tag)
                if field == decoded_tag:
                    model = (value.replace(" ", "")).lower()
        return model
