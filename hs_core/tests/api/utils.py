from django.core.files.uploadedfile import UploadedFile

class MyTemporaryUploadedFile(UploadedFile):
    def __init__(self, file=None, name=None, content_type=None, size=None, charset=None, content_type_extra=None):
        super(UploadedFile, self).__init__(file, name)
        self.orig_name = name
        self.size = size
        self.content_type = content_type
        self.charset = charset
        self.content_type_extra = content_type_extra

    def temporary_file_path(self):
        return self.orig_name