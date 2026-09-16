import urllib.request
import zipfile
import io
import os
import shutil

target_dir = r"D:\room-splatting-test"
url = "https://github.com/graphdeco-inria/gaussian-splatting/archive/refs/heads/main.zip"

print(f"Downloading 3DGS repository zip to {target_dir}...")
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    zip_bytes = response.read()

print("Extracting files...")
with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
    z.extractall(target_dir)

extracted_folder = os.path.join(target_dir, "gaussian-splatting-main")
if os.path.exists(extracted_folder):
    for item in os.listdir(extracted_folder):
        s = os.path.join(extracted_folder, item)
        d = os.path.join(target_dir, item)
        if os.path.exists(d):
            if os.path.isdir(d):
                shutil.rmtree(d)
            else:
                os.remove(d)
        shutil.move(s, d)
    os.rmdir(extracted_folder)

print("Done! Files in D:\\room-splatting-test:")
for item in os.listdir(target_dir):
    print(" -", item)
