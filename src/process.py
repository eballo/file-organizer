import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Tuple, Set
from shutil import copyfile
from pathlib import Path
import PIL.Image
from PIL import ExifTags, UnidentifiedImageError


class FileProcessor:

    def process(self, images: List[str], destination):
        self.create_destination(destination)
        self.create_directories(images, destination)
        self.process_in_parallel(images, destination)

    @staticmethod
    def create_destination(directory_name):
        try:
            os.mkdir(directory_name)
        except OSError:
            print("Creation of the directory %s failed" % directory_name)

    def create_directories(self, images, destination):
        sorted_dates = self.get_unique_sorted_dates(images)
        for date, model in sorted_dates:
            if not os.path.isdir(destination + date):
                self.create_destination(destination + date)
            if model:
                if not os.path.isdir(destination + date + os.path.sep + model):
                    self.create_destination(destination + date + os.path.sep + model)

    def get_unique_sorted_dates(self, images: str) -> Set[Tuple[str, str]]:
        unique_dates = set()
        for image in images:
            unique_dates.add(self.modification_date(image))
        return unique_dates

    def process_in_parallel(self, images: List[str], destination: str):
        args = [(image, destination) for image in images]
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(self.move_images, args)
        print(f"[+] All files were moved successfully! ")

    def move_images(self, args: List[Tuple[str, str]]):
        image, destination = args
        date, model = self.modification_date(image)
        if model:
            dest = destination + date + os.path.sep + model + os.path.sep + Path(image).name
        else:
            dest = destination + date + os.path.sep + Path(image).name
        copyfile(image, dest)

    def modification_date(self, file: str) -> Tuple[str, str]:
        t = os.path.getmtime(file)
        date = datetime.fromtimestamp(t)
        date = str(date.year) + '-' + str(date.month).zfill(2) + '-' + str(date.day).zfill(2)
        model = self.get_data(self.get_exif(file), "Model")
        return date, model

    @staticmethod
    def get_exif(image: str) -> dict:
        exif_raw = None
        try:
            img = PIL.Image.open(image)
            exif_raw = img._getexif()
        except UnidentifiedImageError:
            pass
        return exif_raw

    @staticmethod
    def get_data(exif_raw: dict, field: str) -> str:
        model = None
        if exif_raw:
            for tag, value in exif_raw.items():
                decodedTag = ExifTags.TAGS.get(tag, tag)
                if field == decodedTag:
                    model = (value.replace(" ", "")).lower()
        return model
