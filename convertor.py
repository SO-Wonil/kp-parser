import zipfile

with zipfile.ZipFile("test.hwpx", "r") as zip_ref:
    zip_ref.extractall("./test")