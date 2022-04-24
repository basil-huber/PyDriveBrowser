import curses
from pick import Picker

from pydrivebrowser.google_drive import GoogleDriveFileSystem, GoogleDriveBinaryFile, is_folder, has_file_extension
from pydrivebrowser.url_parser import find_file_id_from_url, find_folder_id_from_url


class CliBrowser(GoogleDriveFileSystem):
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
                return self.CreateFile({'id': file['id']})
            else:
                folder_id = file['id']

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
