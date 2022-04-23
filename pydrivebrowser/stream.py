import io

from googleapiclient.http import DEFAULT_CHUNK_SIZE, MediaIoBaseDownload, MediaDownloadProgress


class DownloadStream(io.RawIOBase):
    def __init__(self, request, chunksize=DEFAULT_CHUNK_SIZE):
        super().__init__()
        self.downloader = MediaIoBaseDownload(self, request, chunksize=chunksize)
        self.memory = None
        self.memory_size = 0
        self.done = False
        self.status = None

    def readinto(self, b):
        if self.done:
            return 0
        self.memory = b
        self.status, self.done = self.downloader.next_chunk()
        return self.memory_size

    def write(self, b):
        self.memory_size = min(len(b),  len(self.memory))
        self.memory[:self.memory_size] = b

    def readable(self) -> bool:
        return True


class GDriveFileReader(io.BufferedReader):
    def __init__(self, request, buffer_size=DEFAULT_CHUNK_SIZE):
        super().__init__(DownloadStream(request, buffer_size), buffer_size)

    @property
    def progress(self) -> MediaDownloadProgress:
        return self.raw.status
