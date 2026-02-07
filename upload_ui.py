#!/usr/bin/env python3
import paramiko
import sys

# Read local file
print("📖 Reading local file...")
with open(r"z:\chefport-bot\web\miniapp_client.html", "r", encoding="utf-8") as f:
    content = f.read()

print(f"✅ Loaded {len(content)} bytes, {content.count(chr(10))} lines")

# SSH Connection
print("🔌 Connecting to server...")
host = "178.208.94.183"
username = "root"
password = "wuMgSXGx9f"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password, timeout=10)
    print("✅ Connected to server")
    
    # Upload via SFTP
    print("📤 Uploading file...")
    sftp = ssh.open_sftp()
    
    # Write to temporary file first
    temp_path = "/tmp/miniapp_client_new.html"
    final_path = "/root/chefport-bot/web/miniapp_client.html"
    
    with sftp.open(temp_path, "w") as remote_file:
        remote_file.write(content)
    
    print(f"✅ Uploaded to {temp_path}")
    
    # Move to final location
    stdin, stdout, stderr = ssh.exec_command(f"mv {temp_path} {final_path} && wc -l {final_path}")
    result = stdout.read().decode()
    print(f"✅ Moved to {final_path}")
    print(f"📊 Result: {result.strip()}")
    
    sftp.close()
    ssh.close()
    
    print("\n🎉 SUCCESS! File uploaded and replaced.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
