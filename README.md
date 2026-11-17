# Ansible Lab - MongoDB Cluster on AWS

Dự án tự động hóa triển khai cơ sở hạ tầng cụm MongoDB Replica Set trên AWS sử dụng CloudFormation, cấu hình SSH tự động và Ansible.

## 🗂️ Cấu trúc thư mục dự án

```
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
```

## 🚀 Hướng dẫn cài đặt và triển khai chi tiết

### 1. Clone dự án và di chuyển vào thư mục làm việc

```
git clone https://github.com/vansonisme/nt542-ansible-lab && cd nt542-ansible-lab
```

### 2. Thiết lập môi trường Python & Cài đặt thư viện

Tạo và kích hoạt môi trường ảo Python để chạy các script tự động hóa:

```
# Tạo môi trường ảo
python3 -m venv .venv

# Kích hoạt môi trường ảo
source .venv/bin/activate

# Cài đặt thư viện cần thiết (boto3 để giao tiếp với AWS)
pip install boto3
```

### 3. Triển khai hạ tầng AWS CloudFormation

Triển khai cụm máy chủ ảo từ template có sẵn bằng AWS CLI:

```
aws cloudformation deploy \
  --template-file infrastructure/mongodb-cluster.yaml \
  --stack-name mongodb-cluster \
  --region us-east-1 \
  --parameter-overrides KeyName=<your-key-pair-name>
```

### 4. Cấu hình quyền cho file khóa (PEM)

Đảm bảo file private key đúng quyền bảo mật yêu cầu của SSH:

```
chmod 400 <key-pair-path>
```

### 5. Tự động cập nhật file `~/.ssh/config`

Chạy script Python để tự động lấy danh sách IP Public mới nhất từ AWS CloudFormation và ghi đè vào cấu hình SSH:

```
python3 add_ssh.py --stack mongodb-cluster --identity_file <key-pair-path>
```

### 6. Kiểm tra kết nối SSH và Ansible

Kiểm tra kết nối trực tiếp qua SSH hoặc kiểm tra toàn bộ cụm bằng Ansible:

```
# Kiểm tra SSH vào từng node (mongodb1 -> mongodb5)
ssh mongodb1

# Kiểm tra kết nối Ansible tới toàn bộ inventory
ansible all -m ping
```

### 7. Chạy Ansible Playbooks để cài đặt và cấu hình MongoDB

Thực thi lần lượt các playbook để cài đặt MongoDB và khởi tạo cụm Replica Set:

```
# Bước 1: Cài đặt MongoDB trên các node
ansible-playbook playbooks/01_install_mongodb.yaml

# Bước 2: Cấu hình Replica Set và bảo mật keyfile
ansible-playbook playbooks/02_replica_set_config.yaml
```

### 8. Rolling upgrade from MongoDB 6.0 to 7.0

After Question 1 is complete, confirm that every member runs MongoDB 6.0,
the replica set has one PRIMARY and four healthy SECONDARY members, and FCV is
6.0. Before running the playbook, load the existing admin password into the WSL environment without putting it in shell history:

    read -rsp "MongoDB admin password: " MONGODB_ADMIN_PASSWORD; export MONGODB_ADMIN_PASSWORD; printf "\\n"

Then run the Question 2 playbook:

    ansible-playbook playbooks/03_upgrade_mongodb.yaml

The playbook checks cluster health and the starting version, discovers the
current Primary, upgrades Secondaries one at a time, steps down and upgrades
the former Primary last, waits for each member to rejoin, verifies all five
binaries are on MongoDB 7.0, then raises FCV to 7.0. The demonstrated patch
version is pinned in group_vars/mongodb.yaml.

Do not rerun the initial installation or replica-set playbooks as part of this
rolling upgrade. Check replica-set health and versions after the play completes.

Platform note: the provided CloudFormation template creates Ubuntu 24.04
instances and the lab uses MongoDB 7.0 packages from the Jammy repository.
MongoDB's official platform matrix does not list MongoDB 7.0 on Ubuntu 24.04;
this setup is for the course exercise and is not an officially supported
production combination.
