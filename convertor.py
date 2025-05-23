import zipfile

with zipfile.ZipFile("test2.hwpx", "r") as zip_ref:
    zip_ref.extractall("./test2")