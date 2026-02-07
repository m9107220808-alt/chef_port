import paramiko

# SSH Connection
host = "178.208.94.183"
username = "root"
password = "wuMgSXGx9f"

# Read local file
with open(r"z:\chefport-bot\web\miniapp_client.html", "r", encoding="utf-8") as f:
    content = f.read()

# Connect and upload
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=username, password=password)

sftp = ssh.open_sftp()
with sftp.open("/root/chefport-bot/web/miniapp_client.html", "w") as remote_file:
    remote_file.write(content)

sftp.close()
ssh.close()

print("✅ File uploaded successfully!")
print(f"   Size: {len(content)} bytes")
print(f"   Lines: {content.count(chr(10)) + 1}")
