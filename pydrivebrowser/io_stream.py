import io

import googleapiclient
from googleapiclient.http import DEFAULT_CHUNK_SIZE, MediaDownloadProgress


class DownloadStream(io.RawIOBase):
    def __init__(self, request: googleapiclient.http.HttpRequest, chunksize=DEFAULT_CHUNK_SIZE):
        super().__init__()
        self._downloader = googleapiclient.http.MediaIoBaseDownload(self, request, chunksize=chunksize)
        self._memory = None
        self._memory_size = 0
        self._done = False
        self.status = None

    def readinto(self, b) -> int:
        if self._done:
            return 0
        self._memory = b
        self.status, self._done = self._downloader.next_chunk()
        return self._memory_size

    def write(self, b):
        if len(b) > len(self._memory):
            raise BufferError(f'Trying to write {len(b)} bytes. Buffer only holds {len(self._memory)} bytes')
        self._memory_size = len(b)
        self._memory[:self._memory_size] = b

    def readable(self) -> bool:
        return True

    def tell(self) -> int:
        if self.status:
            return self.status.resumable_progress
        else:
            return 0


class GDriveFileReader(io.BufferedReader):
    def __init__(self, request: googleapiclient.http.HttpRequest, buffer_size=DEFAULT_CHUNK_SIZE):
        super().__init__(DownloadStream(request, buffer_size), buffer_size)

    @property
    def progress(self) -> MediaDownloadProgress:
        if not self.raw.status:
            self.peek(0)  # download one chunk to know size
        return self.raw.status
