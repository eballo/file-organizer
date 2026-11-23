import os
import shutil
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

from PIL import Image

from src.metadata import (
    CameraName,
    ExifParser,
    ImageMetadataReader,
    Metadata,
    MetadataExtractor,
    MetadataReader,
    VideoMetadataReader,
)


def make_jpeg(path, **tags):
    img = Image.new("RGB", (4, 4))
    exif = Image.Exif()
    exif_ifd = {}
    for name, value in tags.items():
        if name in ("Make", "Model", "DateTime"):
            exif[{"Make": 271, "Model": 272, "DateTime": 306}[name]] = value
        else:
            exif_ifd[{"DateTimeOriginal": 36867, "DateTimeDigitized": 36868}[name]] = value
    if exif_ifd:
        exif[0x8769] = exif_ifd
    img.save(path, exif=exif)


class NamesTest(unittest.TestCase):
    def test_clean_name_removes_unsafe_characters(self):
        self.assertEqual(CameraName.clean("Canon/EOS 60D\x00"), "canoneos60d")
        self.assertEqual(CameraName.clean(b"NIKON D5"), "nikond5")
        self.assertIsNone(CameraName.clean("///"))
        self.assertIsNone(CameraName.clean(42))

    def test_camera_name_combines_make_and_model(self):
        self.assertEqual(CameraName.build("Apple", "iPhone 12"), "apple_iphone12")
        self.assertEqual(CameraName.build("Canon", "Canon EOS 60D"), "canoneos60d")
        self.assertEqual(CameraName.build("OLYMPUS IMAGING CORP.", "Stylus 1"), "olympus_stylus1")
        self.assertEqual(CameraName.build("NIKON CORPORATION", "NIKON D5"), "nikond5")
        self.assertEqual(CameraName.build(None, "Stylus 1"), "stylus1")
        self.assertEqual(CameraName.build("Sony", None), "sony")
        self.assertIsNone(CameraName.build(None, None))

    def test_parse_exif_date(self):
        self.assertEqual(ExifParser.parse_date("2014:03:01 10:11:12"), datetime(2014, 3, 1, 10, 11, 12))
        self.assertEqual(ExifParser.parse_date(b"2014:03:01 10:11:12\x00"), datetime(2014, 3, 1, 10, 11, 12))
        self.assertIsNone(ExifParser.parse_date("0000:00:00 00:00:00"))
        self.assertIsNone(ExifParser.parse_date("garbage"))
        self.assertIsNone(ExifParser.parse_date(None))


class ImageMetadataTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = os.path.join(self._tmp.name, "photo.jpg")

    def test_prefers_original_date_over_file_date_tag(self):
        make_jpeg(self.path, Make="OLYMPUS", Model="Stylus 1", DateTimeOriginal="2014:03:01 10:00:00",
                  DateTime="2020:01:01 00:00:00")
        self.assertEqual(MetadataExtractor().read(self.path), Metadata(datetime(2014, 3, 1, 10), "olympus_stylus1"))

    def test_falls_back_to_digitized_then_datetime(self):
        make_jpeg(self.path, DateTimeDigitized="2015:04:02 08:00:00", DateTime="2020:01:01 00:00:00")
        self.assertEqual(MetadataExtractor().read(self.path).date, datetime(2015, 4, 2, 8))
        make_jpeg(self.path, DateTime="2020:01:01 00:00:00")
        self.assertEqual(MetadataExtractor().read(self.path).date, datetime(2020, 1, 1))

    def test_invalid_date_is_ignored(self):
        make_jpeg(self.path, DateTimeOriginal="0000:00:00 00:00:00", Model="X1")
        self.assertEqual(MetadataExtractor().read(self.path), Metadata(None, "x1"))

    def test_not_an_image_gives_empty_metadata(self):
        with open(self.path, "wb") as f:
            f.write(b"not an image")
        self.assertEqual(MetadataExtractor().read(self.path), Metadata())

    def test_heic_support_is_registered(self):
        self.assertIn("HEIF", Image.registered_extensions().values())


class VideoMetadataTest(unittest.TestCase):
    def setUp(self):
        self.reader = VideoMetadataReader()

    def test_supports_only_video_extensions(self):
        self.assertTrue(self.reader.supports("CLIP.MOV"))
        self.assertFalse(self.reader.supports("photo.jpg"))

    def test_apple_tags_are_preferred(self):
        tags = {"com.apple.quicktime.creationdate": "2023-05-01T12:30:00+0200", "creation_time": "2023-05-01T10:30:00Z"}
        self.assertEqual(self.reader.parse_date(tags), datetime(2023, 5, 1, 12, 30))

    def test_creation_time_is_converted_to_local_time(self):
        expected = datetime.fromisoformat("2023-05-01T10:30:00+00:00").astimezone().replace(tzinfo=None)
        self.assertEqual(self.reader.parse_date({"creation_time": "2023-05-01T10:30:00.000000Z"}), expected)

    def test_unknown_creation_time_is_ignored(self):
        self.assertIsNone(self.reader.parse_date({"creation_time": "1904-01-01T00:00:00Z"}))
        self.assertIsNone(self.reader.parse_date({"creation_time": "nonsense"}))

    def test_without_ffprobe_returns_empty(self):
        with patch("src.metadata.shutil.which", return_value=None):
            self.assertEqual(VideoMetadataReader().read("clip.mp4"), Metadata())

    @unittest.skipUnless(shutil.which("ffprobe"), "ffprobe not installed")
    def test_ffprobe_failure_returns_empty(self):
        self.assertEqual(self.reader.read("/does/not/exist.mp4"), Metadata())


class ExtractorTest(unittest.TestCase):
    def test_first_supporting_reader_wins(self):
        class Fixed(MetadataReader):
            def __init__(self, ext, camera):
                self.ext, self.camera = ext, camera

            def supports(self, path):
                return path.endswith(self.ext)

            def read(self, path):
                return Metadata(None, self.camera)

        extractor = MetadataExtractor([Fixed(".a", "first"), Fixed(".a", "second"), Fixed(".b", "other")])
        self.assertEqual(extractor.read("x.a").camera, "first")
        self.assertEqual(extractor.read("x.b").camera, "other")
        self.assertEqual(extractor.read("x.c"), Metadata())

    def test_default_readers_route_videos_and_images(self):
        readers = MetadataExtractor().readers
        self.assertIsInstance(readers[0], VideoMetadataReader)
        self.assertIsInstance(readers[-1], ImageMetadataReader)


if __name__ == "__main__":
    unittest.main()
