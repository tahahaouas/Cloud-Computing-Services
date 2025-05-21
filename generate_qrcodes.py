import qrcode
import json
import os

BASE_URL = "http://127.0.0.1:5000/found/"

with open("eggs.json") as f:
    eggs = json.load(f)

output_dir = "qrcodes"
os.makedirs(output_dir, exist_ok=True)

for egg in eggs:
    qr = qrcode.make(BASE_URL + egg["id"])
    qr_path = os.path.join(output_dir, f"{egg['id']}.png")
    qr.save(qr_path)
    print(f"QR-Code für {egg['id']} gespeichert unter {qr_path}")
