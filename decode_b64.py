import base64
import sys
import os

files = {
    'web/client_v1_4.b64': 'web/miniapp_client.html',
    'web/admin_v1_4.b64': 'web/miniapp_admin.html'
}

for src, dest in files.items():
    if os.path.exists(src):
        with open(src, 'r') as f:
            b64_data = f.read().strip()
        decoded = base64.b64decode(b64_data)
        with open(dest, 'wb') as f:
            f.write(decoded)
        print(f"Decoded {src} to {dest}")
    else:
        print(f"File not found: {src}")
