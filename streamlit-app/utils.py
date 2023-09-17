import io
import tempfile

class TempFilePath(object):

    def __init__(self, file: io.BytesIO):
        self.file = file
    
    def __enter__(self):
        self.tempFile = tempfile.NamedTemporaryFile(delete=True)
        self.tempFile.write(self.file.read())
        return self.tempFile.name
    
    def __exit__(self, *args):
        self.tempFile.close()
