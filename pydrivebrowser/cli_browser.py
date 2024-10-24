import curses

import pick
from pick import Picker
from pydrive2.files import GoogleDriveFile

from pydrivebrowser.google_drive import GoogleDriveFileSystem, GoogleDriveBinaryFile, is_folder, has_file_extension
from pydrivebrowser.url_parser import find_file_id_from_url, find_folder_id_from_url


class CliBrowser(GoogleDriveFileSystem):
    class PickItem:
        def __init__(self, file: GoogleDriveFile) -> None:
            self.file = file

        def __str__(self) -> str:
            entry = self.file['title'][:CliBrowser.max_file_name_length]
            if 'fileSize' in self.file:
                size = int(self.file['fileSize'])
                entry = entry.ljust(CliBrowser.max_file_name_length, ' ')
                if size < 1024:
                    entry += f'  {size} B'
                elif size < 1024 * 1024:
                    entry += f'  {int(size / 1024)} kiB'
                elif size < 1024 * 1024 * 1024:
                    entry += f'  {int(size / (1024 * 1024))} MiB'
                else:
                    entry += f'  {int(size / (1024 * 1024 * 1024))} GiB'
            return entry

    max_file_name_length = 40

    def select_file(self, url='', file_extension=None) -> GoogleDriveBinaryFile:
        if url:
            file_id = find_file_id_from_url(url)
            if file_id:
                return self.CreateFile({'id': file_id})

            folder_id = find_folder_id_from_url(url)
        else:
            folder_id = 'root'

        return curses.wrapper(self._select_file, folder_id, file_extension)

    def _select_file(self, screen, folder_id: str, file_extension=None) -> GoogleDriveBinaryFile:
        Picker([''], 'select file').config_curses()  # dummy picker to  configure curses

        while True:
            files = [self.PickItem(f) for f in self.listdir(folder_id) if is_folder(f) or has_file_extension(f, file_extension)]
            default_index = 0
            parent = self._get_parent(folder_id)
            if parent:
                parent['title'] = '..'
                files = [self.PickItem(parent)] + files
                if len(files) > 1:
                    default_index = 1
            picker = Picker(files, title='select file', default_index=default_index)
            item, _ = picker.run_loop(screen, pick.Position(0,0))
            if not is_folder(item.file):
                return self.CreateFile({'id': item.file['id']})
            else:
                folder_id = item.file['id']
