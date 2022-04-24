import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock

from googleapiclient.http import DEFAULT_CHUNK_SIZE, MediaDownloadProgress
from oauth2client.service_account import ServiceAccountCredentials
from pydrive2.auth import GoogleAuth

from pydrivebrowser.google_drive import GoogleDriveFileSystem
from pydrivebrowser.io_stream import DownloadStream, GDriveFileReader


file_level0_id = '1Rqfi4CeakfGx_xWa58Rz3SM2iHVSPzoH'
folder_level0_id = '1APzr67aMpXSkcMNlA0rWaJHvMoXwb9o8'


class GoogleDriveFileSystemTest(TestCase):
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

    def test_open_file_from_id(self):
        gfs = GoogleDriveFileSystem(self.auth)
        file = gfs.CreateFile({'id': file_level0_id})

        reader = file.open()
        self.assertIsInstance(reader, GDriveFileReader)
