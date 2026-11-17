import subprocess
import os
import argparse

# 1. Khởi tạo argparse để nhận tham số từ dòng lệnh
parser = argparse.ArgumentParser(description="Tự động cập nhật ~/.ssh/config từ AWS CloudFormation.")
parser.add_argument(
    "--stack", 
    type=str, 
    default="mongodb-cluster", 
    help="Tên AWS CloudFormation stack"
)
parser.add_argument(
    "--identity_file", 
    type=str, 
    default="/home/son/ansible_lab/4444.pem", 
    help="Đường dẫn tuyệt đối đến file key .pem"
)
parser.add_argument(
    "--user", 
    type=str, 
    default="ubuntu", 
    help="Tên user SSH"
)

args = parser.parse_args()

# 2. Gán giá trị từ tham số truyền vào
stack_name = args.stack
identity_file = args.identity_file
ssh_user = args.user
ssh_config_path = os.path.expanduser("~/.ssh/config")

print(f"Đang lấy danh sách IP Public từ stack '{stack_name}'...")
cmd = [
    "aws", "cloudformation", "describe-stacks",
    "--stack-name", stack_name,
    "--query", "Stacks[0].Outputs[?contains(OutputKey, 'PublicIp')].[OutputKey, OutputValue]",
    "--output", "text"
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
except subprocess.CalledProcessError as e:
    print(f"Lỗi khi chạy AWS CLI: {e.stderr}")
    exit(1)

lines = result.stdout.strip().split("\n")
nodes = {}
for line in lines:
    parts = line.split()
    if len(parts) == 2:
        key, ip = parts
        num = "".join(filter(str.isdigit, key))
        if num:
            nodes[int(num)] = ip

if not nodes:
    print("Không tìm thấy IP Public nào từ CloudFormation stack.")
    exit(1)

sorted_nodes = sorted(nodes.items())

# Đảm bảo thư mục ~/.ssh tồn tại
ssh_dir = os.path.dirname(ssh_config_path)
os.makedirs(ssh_dir, exist_ok=True)

# Đọc file ~/.ssh/config hiện tại (nếu có)
try:
    with open(ssh_config_path, "r") as f:
        config_content = f.read()
except FileNotFoundError:
    config_content = ""

# Xóa các khối cấu hình 'Host mongodb*' cũ để overwrite (ghi đè) sạch sẽ
clean_lines = []
skip = False
for line in config_content.splitlines():
    if line.strip().startswith("Host mongodb"):
        skip = True
    elif skip and (line.strip().startswith("Host ") or line.strip() == ""):
        if line.strip().startswith("Host "):
            skip = False
        else:
            continue
    
    if not skip:
        clean_lines.append(line)

# Tạo các đoạn cấu hình mới với identity_file được truyền vào
new_blocks = []
for num, ip in sorted_nodes:
    block = f"""Host mongodb{num}
    HostName {ip}
    User {ssh_user}
    IdentityFile {identity_file}"""
    new_blocks.append(block)

# Ghép nội dung cũ và các block mới lại với nhau
final_content = "\n".join(clean_lines).strip()
if final_content:
    final_content += "\n\n"
final_content += "\n\n".join(new_blocks) + "\n"

# Ghi đè (overwrite) lại vào file ~/.ssh/config
with open(ssh_config_path, "w") as f:
    f.write(final_content)

print(f"Đã cập nhật thành công các cấu hình SSH vào {ssh_config_path}!")
