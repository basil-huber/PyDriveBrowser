import curses
from typing import List, Dict

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.files import GoogleDriveFile

from pydrivebrowser.url_parser import find_file_id_from_url, find_folder_id_from_url
from pick import Picker


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


class CliBrowser(GoogleDrive):
    max_file_name_length = 40

    def __init__(self, auth=None):
        if not auth:
            auth = self._authenticate()
        super().__init__(auth)

    @staticmethod
    def _authenticate() -> GoogleAuth:
        auth = GoogleAuth()
        # curses wrapper to avoid spamming the console
        curses.wrapper(lambda std_scr: auth.LocalWebserverAuth())
        return auth

    def select_file(self, url='', file_extension=None) -> GoogleDriveFile:
        if url:
            file_id = find_file_id_from_url(url)
            if file_id:
                return self.CreateFile({'id': file_id})

            folder_id = find_folder_id_from_url(url)
        else:
            folder_id = 'root'

        return curses.wrapper(self._select_file, folder_id, file_extension)

    def _select_file(self, screen, folder_id: str, file_extension=None) -> GoogleDriveFile:
        Picker([''], 'select file').config_curses()  # dummy picker to  configure curses

        while True:
            files = [f for f in self.listdir(folder_id) if is_folder(f) or has_file_extension(f, file_extension)]
            default_index = 0
            parent = self._get_parent(folder_id)
            if parent:
                parent['title'] = '..'
                files = [parent] + files
                if len(files) > 1:
                    default_index = 1
            picker = Picker(files, 'select file', default_index=default_index, options_map_func=self._print_file_entry)
            file, _ = picker.run_loop(screen)
            if not is_folder(file):
                return file
            else:
                folder_id = file['id']

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

    @classmethod
    def _print_file_entry(cls, file) -> str:
        entry = file['title'][:cls.max_file_name_length]
        if 'fileSize' in file:
            size = int(file['fileSize'])
            entry = entry.ljust(cls.max_file_name_length, ' ')
            if size < 1024:
                entry += f'  {size} B'
            elif size < 1024*1024:
                entry += f'  {int(size / 1024)} kiB'
            elif size < 1024*1024*1024:
                entry += f'  {int(size / (1024*1024))} MiB'
            else:
                entry += f'  {int(size / (1024 * 1024 * 1024))} GiB'
        return entry
