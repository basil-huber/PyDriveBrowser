import re


file_id_regex = re.compile('file/d/([0-9A-Za-z_-]*)')
folder_id_regex = re.compile('folders/([0-9A-Za-z_-]*)')


def find_file_id_from_url(url: str) -> [str, None]:
    file_id_match = file_id_regex.search(url)
    if file_id_match:
        return file_id_match.group(1)
    return None


def find_folder_id_from_url(url: str) -> [str, None]:
    folder_id_match = folder_id_regex.search(url)
    if folder_id_match:
        return folder_id_match.group(1)
    return None
