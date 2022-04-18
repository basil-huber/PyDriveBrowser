import curses
import json
import os
from unittest import TestCase
from unittest.mock import patch

from oauth2client.service_account import ServiceAccountCredentials
from pick import Picker
from pydrive2.auth import GoogleAuth

from pydrivebrowser.cli_browser import CliBrowser

folder_level0_id = '1APzr67aMpXSkcMNlA0rWaJHvMoXwb9o8'
file_level0_id = '1Rqfi4CeakfGx_xWa58Rz3SM2iHVSPzoH'
folder_level1_id = '1TqzG9-mkyLi69ktCm-VbNzToR5B3UC3w'
file_level1_id = '1Wc2fNOncBSUrb4_aUih9ov_QkQ-wWMku'


def mock_wrapper(*args, **kwargs):
    func, *args = args
    return func(None, *args, **kwargs)


def create_mock_run_loop(*file_ids):
    files = file_ids.__iter__()

    def mock_run_loop(self, screen):
        file_id = next(files)
        for index, option in enumerate(self.options):
            if option['id'] == file_id:
                return option, index
        raise KeyError()

    return mock_run_loop


class CliBrowserTest(TestCase):
    auth = None

    @classmethod
    def _authenticate(cls) -> None:
        cls.auth = GoogleAuth()
        scope = ["https://www.googleapis.com/auth/drive.file",
                 "https://www.googleapis.com/auth/drive"]
        with open('service_account_credentials.json', 'r') as json_file:
            # json_dict = json.load(json_file)
            # json_dict['private_key'] = os.environ['SERVICE_ACCOUNT_PRIVATE_KEY'].replace(r'\n', '\n')
            # cls.auth.credentials = ServiceAccountCredentials.from_json_keyfile_dict(json_dict, scope)
            cls.auth.credentials = ServiceAccountCredentials.from_json_keyfile_name('service_account_credentials.json',
                                                                                    scope)

    @classmethod
    def setUpClass(cls) -> None:
        cls._authenticate()
        cls.commands = []

    @patch.object(Picker, 'config_curses', autospec=True)
    @patch.object(curses, 'wrapper', mock_wrapper)
    def test_file_level_0(self, mock_config_curses):
        url_folder_level_0 = f'https://drive.google.com/drive/folders/{folder_level0_id}?usp=sharing'
        browser = CliBrowser(self.auth)
        with patch.object(Picker, 'run_loop', create_mock_run_loop(file_level0_id)):
            file = browser.select_file(url_folder_level_0)
            self.assertEqual(file_level0_id, file['id'])
            mock_config_curses.assert_called()

    @patch.object(Picker, 'config_curses', autospec=True)
    @patch.object(curses, 'wrapper', mock_wrapper)
    def test_file_level_1(self, mock_config_curses):
        url_folder_level_0 = 'https://drive.google.com/drive/folders/1APzr67aMpXSkcMNlA0rWaJHvMoXwb9o8?usp=sharing'
        browser = CliBrowser(self.auth)

        with patch.object(Picker, 'run_loop', create_mock_run_loop(folder_level1_id, file_level1_id)):
            file = browser.select_file(url_folder_level_0)
            self.assertEqual(file_level1_id, file['id'])
            mock_config_curses.assert_called()

    @patch.object(Picker, 'config_curses', autospec=True)
    @patch.object(curses, 'wrapper', mock_wrapper)
    def test_file_level_0_from_level_1(self, mock_config_curses):
        url_folder_level_1 = f'https://drive.google.com/drive/folders/{folder_level1_id}?usp=sharing'
        browser = CliBrowser(self.auth)

        with patch.object(Picker, 'run_loop', create_mock_run_loop(folder_level0_id, file_level0_id)):
            file = browser.select_file(url_folder_level_1)
            self.assertEqual(file_level0_id, file['id'])
            mock_config_curses.assert_called()
