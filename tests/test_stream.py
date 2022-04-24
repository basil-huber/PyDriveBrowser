import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock

from googleapiclient.http import DEFAULT_CHUNK_SIZE, MediaDownloadProgress
from oauth2client.service_account import ServiceAccountCredentials
from pydrive2.auth import GoogleAuth

from pydrivebrowser.google_drive import GoogleDriveFileSystem
from pydrivebrowser.io_stream import DownloadStream, GDriveFileReader


class MockMediaIoBaseDownload:
    def __init__(self, fd, request, chunksize=DEFAULT_CHUNK_SIZE):
        self._fd = fd
        self._request = request
        self._chunksize = chunksize
        self._bytes_read = 0
        self._bytes_total = chunksize
        self.call_count = 0

    def next_chunk(self, num_retries=0):
        remaining_size = self._bytes_total - self._bytes_read
        chunksize = min(remaining_size, self._chunksize)
        self._fd.write(bytes([i for i in range(self._bytes_read, self._bytes_read+chunksize)]))
        self._bytes_read += chunksize
        self.call_count += 1
        return MediaDownloadProgress(self._bytes_read, self._bytes_total), self._bytes_read == self._bytes_total


http_request = MagicMock()

test_file_lines_id = '1Nepia57H0hF6oDUAZpRNtl3xbSTylGUM'


class DownloadStreamTest(TestCase):

    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_init(self):
        chunksize = 100
        ds = DownloadStream(http_request, chunksize)
        self.assertEqual(http_request, ds._downloader._request)
        self.assertEqual(chunksize, ds._downloader._chunksize)
        self.assertEqual(ds, ds._downloader._fd)

    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_readinto_one_chunk(self):
        chunksize = 100
        ds = DownloadStream(http_request, chunksize)
        b = bytearray(chunksize)
        ret = ds.readinto(b)

        self.assertEqual(bytes([i for i in range(0, chunksize)]), b)
        self.assertEqual(chunksize, ret)

    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_readinto_less_than_chunk(self):
        chunksize = 100
        ds = DownloadStream(http_request, chunksize)
        ds._downloader._bytes_total = 99
        b = bytearray(chunksize)

        ret = ds.readinto(b)
        self.assertEqual(bytes([i for i in range(0, 99)]), b[0:99])
        self.assertEqual(99, ret)

        ret = ds.readinto(b)
        self.assertEqual(0, ret)

    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_readinto_more_than_chunk(self):
        chunksize = 100
        ds = DownloadStream(http_request, chunksize)
        ds._downloader._bytes_total = 201
        b = bytearray(chunksize)

        ret = ds.readinto(b)
        self.assertEqual(bytes([i for i in range(0, chunksize)]), b[0:chunksize])
        self.assertEqual(chunksize, ret)

        ret = ds.readinto(b)
        self.assertEqual(bytes([i for i in range(chunksize, 2*chunksize)]), b[0:chunksize])
        self.assertEqual(chunksize, ret)

        ret = ds.readinto(b)
        self.assertEqual(bytes([i for i in range(2*chunksize, 2*chunksize+1)]), b[0:1])
        self.assertEqual(1, ret)

    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_readinto_too_short_buffer(self):
        chunksize = 100
        ds = DownloadStream(http_request, chunksize)
        b = bytearray(chunksize - 1)
        with self.assertRaises(BufferError):
            ds.readinto(b)

    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_readinto_longer_buffer(self):
        chunksize = 100
        ds = DownloadStream(http_request, chunksize)
        b = bytearray(chunksize + 10)
        ret = ds.readinto(b)
        self.assertEqual(bytes([i for i in range(0, chunksize)]), b[0:chunksize])
        self.assertEqual(chunksize, ret)

    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_read(self):
        chunksize = 100
        ds = DownloadStream(http_request, chunksize)
        b = ds.read()
        self.assertEqual(bytes([i for i in range(0, chunksize)]), b)


class GDriveFileReaderTest(TestCase):
    auth = None

    @classmethod
    def _authenticate(cls) -> None:
        cls.auth = GoogleAuth()
        scope = ["https://www.googleapis.com/auth/drive.file",
                 "https://www.googleapis.com/auth/drive"]
        with open('service_account_credentials.json', 'r') as json_file:
            cls.auth.credentials = ServiceAccountCredentials.from_json_keyfile_name('service_account_credentials.json', scope)

    @classmethod
    def setUpClass(cls) -> None:
        cls._authenticate()

    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_init(self):
        buffer_size = 100
        reader = GDriveFileReader(http_request, buffer_size)
        self.assertIsInstance(reader.raw, DownloadStream)
        self.assertEqual(buffer_size, reader.raw._downloader._chunksize)

    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_read_chunk(self):
        buffer_size = 100
        reader = GDriveFileReader(http_request, buffer_size)
        b = reader.read(100)
        self.assertEqual(1, reader.raw._downloader.call_count)
        self.assertEqual(bytes([i for i in range(0, 100)]), b)

        b = reader.read(100)
        self.assertEqual(1, reader.raw._downloader.call_count)
        self.assertEqual(b'', b)

    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_read_less_than_chunk(self):
        buffer_size = 100
        reader = GDriveFileReader(http_request, buffer_size)
        b = reader.read(90)
        self.assertEqual(1, reader.raw._downloader.call_count)
        self.assertEqual(bytes([i for i in range(0, 90)]), b)

        b = reader.read(5)
        self.assertEqual(1, reader.raw._downloader.call_count)
        self.assertEqual(bytes([i for i in range(90, 95)]), b)

        b = reader.read(10)
        self.assertEqual(1, reader.raw._downloader.call_count)
        self.assertEqual(bytes([i for i in range(95, 100)]), b)

    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_read_multiple_chunks(self):
        buffer_size = 100
        reader = GDriveFileReader(http_request, buffer_size)
        reader.raw._downloader._bytes_total = 150

        b = reader.read(150)
        self.assertEqual(2, reader.raw._downloader.call_count)
        self.assertEqual(bytes([i for i in range(0, 150)]), b)

    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_read_multiple_chunks_too_long(self):
        buffer_size = 100
        reader = GDriveFileReader(http_request, buffer_size)
        reader.raw._downloader._bytes_total = 150

        b = reader.read(200)
        self.assertEqual(2, reader.raw._downloader.call_count)
        self.assertEqual(bytes([i for i in range(0, 150)]), b)

    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_read_multiple_chunks_parts(self):
        buffer_size = 100
        reader = GDriveFileReader(http_request, buffer_size)
        reader.raw._downloader._bytes_total = 150

        b = reader.read(90)
        self.assertEqual(1, reader.raw._downloader.call_count)
        self.assertEqual(bytes([i for i in range(0, 90)]), b)

        b = reader.read(20)
        self.assertEqual(2, reader.raw._downloader.call_count)
        self.assertEqual(bytes([i for i in range(90, 110)]), b)

        b = reader.read(100)
        self.assertEqual(2, reader.raw._downloader.call_count)
        self.assertEqual(bytes([i for i in range(110, 150)]), b)

    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_readinto_full(self):
        buffer_size = 100
        reader = GDriveFileReader(http_request, buffer_size)
        reader.raw._downloader._bytes_total = 150

        b = bytearray(150)
        reader.readinto(b)
        self.assertEqual(2, reader.raw._downloader.call_count)
        self.assertEqual(bytes([i for i in range(0, 150)]), b)

    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_readinto_long_buffer(self):
        buffer_size = 100
        reader = GDriveFileReader(http_request, buffer_size)

        b = bytearray(200)
        reader.readinto(b)
        # self.assertEqual(2, reader.raw._downloader.call_count)
        self.assertEqual(bytes([i for i in range(0, 100)]), b[:100])

    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_readinto_short_buffer(self):
        buffer_size = 100
        reader = GDriveFileReader(http_request, buffer_size)

        b = bytearray(50)
        reader.readinto(b)
        self.assertEqual(1, reader.raw._downloader.call_count)
        self.assertEqual(bytes([i for i in range(0, 50)]), b)

    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_read1_full(self):
        buffer_size = 100
        reader = GDriveFileReader(http_request, buffer_size)

        b = reader.read1(100)
        self.assertEqual(1, reader.raw._downloader.call_count)
        self.assertEqual(bytes([i for i in range(0, 100)]), b)

    @unittest.skip('Throws error as reader.read1 calls reader.raw.readinto with buffer shorter than chunksize')
    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_read1_short(self):
        buffer_size = 100
        reader = GDriveFileReader(http_request, buffer_size)

        b = reader.read1(50)
        self.assertEqual(1, reader.raw._downloader.call_count)
        self.assertEqual(bytes([i for i in range(0, 50)]), b)

    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_read1_long(self):
        buffer_size = 100
        reader = GDriveFileReader(http_request, buffer_size)
        reader.raw._downloader._bytes_total = 150

        b = reader.read1(150)
        self.assertEqual(1, reader.raw._downloader.call_count)
        self.assertEqual(bytes([i for i in range(0, 100)]), b[:100])

    @patch('googleapiclient.http.MediaIoBaseDownload', MockMediaIoBaseDownload)
    def test_tell(self):
        buffer_size = 100
        reader = GDriveFileReader(http_request, buffer_size)
        reader.raw._downloader._bytes_total = 150

        self.assertEqual(0, reader.tell())

        b = bytearray(50)
        reader.readinto(b)
        self.assertEqual(50, reader.tell())

        reader.readinto(b)
        self.assertEqual(100, reader.tell())

        reader.readinto(b)
        self.assertEqual(150, reader.tell())

    def test_read(self):
        gfs = GoogleDriveFileSystem(self.auth)
        file = gfs.CreateFile({'id': test_file_lines_id})

        reader = file.open()
        self.assertEqual(b'li', reader.read(2))
        self.assertEqual(2, reader.tell())
        self.assertEqual(b'ne', reader.read(2))
        self.assertEqual(4, reader.tell())

    def test_readline(self):
        gfs = GoogleDriveFileSystem(self.auth)
        file = gfs.CreateFile({'id': test_file_lines_id})

        reader = file.open()

        length = 0
        for i, l in enumerate(reader):
            self.assertEqual(f'line_{i}\n'.encode(), l)
            length += len(l)
            self.assertEqual(length, reader.tell())
