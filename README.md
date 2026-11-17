# Ansible Lab - MongoDB Cluster on AWS

Dự án tự động hóa triển khai cơ sở hạ tầng cụm MongoDB Replica Set trên AWS sử dụng CloudFormation, cấu hình SSH tự động và Ansible.

## 🗂️ Cấu trúc thư mục dự án

```text
├── .env.example
├── add_ssh.py
├── ansible.cfg
├── group_vars
│   └── mongodb.yaml
├── hosts.ini
├── infrastructure
│   └── mongodb-cluster.yaml
└── playbooks
    ├── 01_install_mongodb.yaml
    ├── 02_replica_set_config.yaml
    └── 03_upgrade_mongodb.yaml
```

## 🚀 Hướng dẫn cài đặt và triển khai chi tiết

### 1. Clone dự án và di chuyển vào thư mục làm việc

```bash
git clone https://github.com/vansonisme/nt542-ansible-lab && cd nt542-ansible-lab
```

### 2. Thiết lập môi trường Python & Cài đặt thư viện

Tạo và kích hoạt môi trường ảo Python để chạy các script tự động hóa:

```bash
# Tạo môi trường ảo
python3 -m venv .venv

# Kích hoạt môi trường ảo
source .venv/bin/activate

# Cài đặt thư viện cần thiết (boto3 để giao tiếp với AWS)
pip install boto3
```

### 3. Cấu hình biến môi trường (`.env`)

Tạo file `.env` từ file mẫu và điền mật khẩu quản trị MongoDB của bạn:

```bash
cp .env.example .env
```

Mở file `.env` và cập nhật giá trị `MONGODB_ADMIN_PASSWORD`:

```env
MONGODB_ADMIN_PASSWORD="<your-admin-password>"
```

### 4. Triển khai hạ tầng AWS CloudFormation

Triển khai cụm máy chủ ảo từ template có sẵn bằng AWS CLI:

```bash
aws cloudformation deploy \
  --template-file infrastructure/mongodb-cluster.yaml \
  --stack-name mongodb-cluster \
  --region us-east-1 \
  --parameter-overrides KeyName=<your-key-pair-name>
```

### 5. Cấu hình quyền cho file khóa (PEM)

Đảm bảo file private key đúng quyền bảo mật yêu cầu của SSH:

```bash
chmod 400 <key-pair-path>
```

### 6. Tự động cập nhật file `~/.ssh/config`

Chạy script Python để tự động lấy danh sách IP Public mới nhất từ AWS CloudFormation và ghi đè vào cấu hình SSH:

```bash
python3 add_ssh.py --stack mongodb-cluster --identity_file <key-pair-path>
```

### 7. Kiểm tra kết nối SSH và Ansible

Kiểm tra kết nối trực tiếp qua SSH hoặc kiểm tra toàn bộ cụm bằng Ansible:

```bash
# Kiểm tra SSH vào từng node (mongodb1 -> mongodb5)
ssh mongodb1

# Kiểm tra kết nối Ansible tới toàn bộ inventory
ansible all -m ping
```

### 8. Chạy Ansible Playbooks để cài đặt và cấu hình MongoDB

Thực thi lần lượt các playbook để cài đặt MongoDB và khởi tạo cụm Replica Set:

```bash
# Bước 1: Cài đặt MongoDB trên các node
ansible-playbook playbooks/01_install_mongodb.yaml

# Bước 2: Cấu hình Replica Set và bảo mật keyfile
ansible-playbook playbooks/02_replica_set_config.yaml
```

### 9. Nâng cấp cuốn chiếu (Rolling Upgrade) từ MongoDB 6.0 lên 7.0

Sau khi hoàn tất bước cài đặt ban đầu, hãy đảm bảo tất cả các node đều đang chạy MongoDB 6.0, cụm Replica Set có 1 node `PRIMARY` cùng 4 node `SECONDARY` hoạt động ổn định, và mức tương thích tính năng (`FCV`) đang là `6.0`. 

Trước khi chạy playbook nâng cấp, nạp biến môi trường từ file `.env` đã cấu hình ở Bước 3 vào phiên làm việc hiện tại:

```bash
set -a && source .env && set +a
```

Sau đó, chạy playbook nâng cấp:

```bash
ansible-playbook playbooks/03_upgrade_mongodb.yaml
```

**Cơ chế hoạt động của playbook:**
* Kiểm tra tình trạng cụm và phiên bản hiện tại.
* Xác định node `PRIMARY` hiện hành.
* Nâng cấp lần lượt từng node `SECONDARY`, sau đó thực hiện hạ cấp (step down) và nâng cấp node `PRIMARY` cũ sau cùng.
* Chờ từng node gia nhập lại cụm sau khi nâng cấp, xác minh cả 5 node đều đã lên MongoDB 7.0 (phiên bản cụ thể được ghim trong `group_vars/mongodb.yaml`), rồi mới nâng `FCV` lên `7.0`.

> **Lưu ý:** 
> * **Không** chạy lại các playbook cài đặt ban đầu (`01` và `02`) trong quá trình nâng cấp này. Hãy kiểm tra lại trạng thái cụm và phiên bản trên các node sau khi playbook hoàn tất.
> * **Tương thích hệ điều hành:** Template CloudFormation sử dụng Ubuntu 24.04 trong khi bài lab cài đặt gói MongoDB 7.0 từ repository của Ubuntu 22.04 (Jammy). Bảng hỗ trợ chính thức của MongoDB không liệt kê MongoDB 7.0 trên Ubuntu 24.04; cấu hình này chỉ phục vụ mục đích thực hành môn học, không khuyến nghị dùng cho môi trường production.
