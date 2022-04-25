import os
from typing import List, Dict

from pydrive2.files import FileNotUploadedError, GoogleDriveFile
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from pydrivebrowser.io_stream import GDriveFileReader
from pydrivebrowser.url_parser import find_file_id_from_url

try:
    from curses import wrapper
    if 'TERM' not in os.environ:
        raise ValueError('No terminal')
except (ImportError, ValueError):
    def wrapper(func, *args, **kwargs):
        return func(None, *args, **kwargs)


class GoogleDriveBinaryFile(GoogleDriveFile):
    def open(self) -> GDriveFileReader:
        files = self.auth.service.files()
        file_id = self.metadata.get("id") or self.get("id")
        if not file_id:
            raise FileNotUploadedError()
        request = self._WrapRequest(files.get_media(fileId=file_id))
        return GDriveFileReader(request)

    def close(self):
        pass


def is_folder(file: GoogleDriveFile):
    return 'folder' in file['mimeType']


def has_file_extension(file: GoogleDriveFile, extension: str):
    split_list = file['title'].split('.')
    if extension is None:
        return True
    elif extension == '':
        if len(split_list) <= 1:
            return True
        else:
            return False
    return len(split_list) > 1 and split_list[-1] == extension


class GoogleDriveFileSystem(GoogleDrive):

    def __init__(self, auth=None):
        if not auth:
            auth = GoogleAuth()
        self._authenticate(auth)
        super().__init__(auth)
        self.auth.Authorize()

    def open(self, filename: str) -> GDriveFileReader:
        """
        Open a file on Google Drive

        :param filename: fileID or URL
        :return: GDriveFileReader (file-like buffered reader)

        :raises:
        """
        file_id = find_file_id_from_url(filename)
        if not file_id:
            file_id = filename
        return self.CreateFile({'id': file_id}).open()

    @staticmethod
    def _authenticate(auth) -> None:
        if not auth.credentials:
            # curses wrapper to avoid spamming the console
            wrapper(lambda std_scr: auth.LocalWebserverAuth())

    def listdir(self, folder_id: str) -> List:
        return self.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()

    def _get_parent(self, file_id: str) -> [Dict, None]:
        parents = self.CreateFile({'id': file_id})['parents']
        if parents:
            parent = parents[0]
            parent['mimeType'] = 'folder'
            return parent
        else:
            return None

    def CreateFile(self, metadata=None) -> GoogleDriveBinaryFile:
        return GoogleDriveBinaryFile(auth=self.auth, metadata=metadata)
