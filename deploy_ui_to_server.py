#!/usr/bin/env python3
"""
Quick script to upload miniapp_client.html to the server via SSH/SFTP
"""
import paramiko
import sys
from pathlib import Path

# Configuration
HOST = "178.208.94.183"
USERNAME = "root"
PASSWORD = "wuMgSXGx9f"
LOCAL_FILE = r"z:\chefport-bot\web\miniapp_client.html"
REMOTE_FILE = "/root/chefport-bot/web/miniapp_client.html"

def main():
    print("🚀 Deploying Premium UI to server...")
    
    # Check local file exists
    local_path = Path(LOCAL_FILE)
    if not local_path.exists():
        print(f"❌ Local file not found: {LOCAL_FILE}")
        sys.exit(1)
    
    file_size = local_path.stat().st_size
    print(f"📄 Local file: {LOCAL_FILE} ({file_size} bytes)")
    
    # Connect via SSH
    print(f"🔌 Connecting to {HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(HOST, username=USERNAME, password=PASSWORD, timeout=15)
        print("✅ Connected!")
        
        # Upload via SFTP
        print(f"📤 Uploading to {REMOTE_FILE}...")
        sftp = ssh.open_sftp()
        sftp.put(LOCAL_FILE, REMOTE_FILE)
        sftp.close()
        print("✅ Upload complete!")
        
        # Verify
        stdin, stdout, stderr = ssh.exec_command(f"wc -l {REMOTE_FILE}")
        result = stdout.read().decode().strip()
        print(f"📊 Server file: {result}")
        
        ssh.close()
        print("\n🎉 SUCCESS! Premium UI deployed to server.")
        print("\nNext steps:")
        print("1. Test the site: http://178.208.94.183:8000/web/miniapp_client.html")
        print("2. Or restart bot service if needed: systemctl restart chefport-bot.service")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
