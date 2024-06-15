import io
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Tuple, Set, Optional
from shutil import copyfile
from pathlib import Path
from PIL import Image, ExifTags, UnidentifiedImageError, ImageFile
from PIL.Image import Exif
import logging
from tqdm import tqdm


class FileProcessor:

    def __init__(self):
        self.progress_bar_reading = None
        self.progress_bar_directories = None
        self.progress_bar_files = None

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

        self._copy_file(image, destination)
        self.progress_bar_files.update()

    def _copy_file(self, image, destination):
        copyfile(image, destination + Path(image).name)

    def modification_date(self, file: str) -> Tuple[str, str]:
        exif_raw, date = self._modify_date(file)
        model = self.get_data(exif_raw, "Model")
        date = str(date.year) + '-' + str(date.month).zfill(2) + '-' + str(date.day).zfill(2)
        return date, model

    def _modify_date(self, file):
        t = os.path.getmtime(file)
        date = datetime.fromtimestamp(t)
        exif_raw = self.get_exif(file)
        return exif_raw, date

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


class FileProcessorWin32(FileProcessor):
    """
    This class holds the specific logic needed for win32
    """

    def _copy_file(self, image, destination):
        import src.mtp_windows

        cont = src.mtp_windows.get_content_from_device_path(image)
        target_file = open(destination + cont.getName(), "wb")
        cont.downloadStream(target_file)
        target_file.close()

    def _modify_date(self, file):
        exif_raw = None
        date = datetime.today()
        try:
            import src.mtp_windows

            cont = src.mtp_windows.get_content_from_device_path(file)
            buffer = cont.read_data()
            byte_imge_io = io.BytesIO(buffer)
            byte_imge_io.seek(0)
            byte_image = byte_imge_io.read()
            img = Image.open(io.BytesIO(byte_image))
            exif_raw = img.getexif()
            date = cont.getDate()
        except Exception as e:
            logging.error(e)
        return exif_raw, date
