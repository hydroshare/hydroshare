
def check_upload_files(resource_cls, fnames_list):
    file_types = resource_cls.get_supported_upload_file_types()
    valid = False
    ext = ''
    if file_types == ".*":
        valid = True
    else:
        for fname in fnames_list:
            ext = os.path.splitext(fname)[1].lower()
            if ext == file_types:
                valid = True
            else:
                for index in range(len(file_types)):
                    file_type_str = file_types[index].strip().lower()
                    if file_type_str == ".*" or ext == file_type_str:
                        valid = True
                        break

    return (valid, ext)
