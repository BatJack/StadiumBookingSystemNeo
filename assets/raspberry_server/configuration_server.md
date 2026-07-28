# 服务器配置指南 - Gunicorn + Nginx 部署 Django 项目

本文档介绍如何在 Linux 服务器上使用 Gunicorn 和 Nginx 部署 Django 项目。

## 环境说明

- **Python 版本**：Python 3.12+
- **网站端口**：80（HTTP）、443（HTTPS）

---

## 第一步：安装必要软件

### 1.1 更新软件包列表

```bash
sudo apt update
```

### 1.2 安装软件

```bash
sudo apt install -y nginx git
```

### 1.3 验证安装

```bash
# 检查 Nginx 版本
nginx -v

# 检查 Git 版本
git --version
```

---

## 第二步：上传项目文件

### 2.1 创建项目目录

**使用 Git 克隆**

```bash
# 如果有 Git 仓库
git clone https://github.com/BatJack/StaduimBookingSystem.git

### 验证文件上传

```bash
cd ~/StaduimBookingSystem
ls -la
```

应该看到以下文件和目录：

```
db.sqlite3
manage.py
stadium_booking/
booking/
requirements.txt
```

---

## 第三步：配置虚拟环境

### 3.1 创建虚拟环境

```bash
cd ~/StaduimBookingSystem
python3 -m venv venv
```

### 3.2 激活虚拟环境

```bash
source venv/bin/activate
```

激活后，命令行前面会出现 `(venv)` 标记：

```
(venv) user@server:~/StaduimBookingSystem$
```

### 3.3 安装依赖

```bash
# 如果有 requirements.txt
pip install -r requirements.txt

# 如果没有，手动安装
pip install django gunicorn
```

### 3.4 验证安装

```bash
# 检查 Django
python -c "import django; print(django.__version__)"

# 检查 Gunicorn
gunicorn --version
```

---

## 第四步：配置 Django 项目

### 4.1 修改 settings.py

编辑 `stadium_booking/settings.py`：

```bash
nano ~/StaduimBookingSystem/stadium_booking/settings.py
```

找到并修改以下内容：

```python
# 允许所有主机访问（测试用）
ALLOWED_HOSTS = ['*']

# 添加静态文件配置
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

### 4.2 执行数据库迁移

```bash
cd ~/StaduimBookingSystem
source venv/bin/activate
python manage.py migrate
```

### 4.3 创建管理员账户

```bash
python manage.py creat_user_cli.py
```

按照提示输入用户名、邮箱、密码。

### 4.4 收集静态文件

```bash
python manage.py collectstatic
```

### 4.5 测试运行

```bash
python manage.py runserver 0.0.0.0:8000
```

在浏览器访问 `http://服务器IP:8000`，应该能看到网站。

按 `Ctrl+C` 停止测试服务器。

---

## 第五步：测试 Gunicorn

### 5.1 启动 Gunicorn

```bash
cd ~/StaduimBookingSystem
source venv/bin/activate
gunicorn --bind 0.0.0.0:8000 stadium_booking.wsgi:application
```

### 5.2 测试访问

打开浏览器访问：`http://服务器IP:8000`

### 5.3 停止 Gunicorn

按 `Ctrl+C` 停止。

### 5.4 创建 Gunicorn 配置文件（可选）

```bash
nano ~/StaduimBookingSystem/gunicorn.conf.py
```

内容：

```python
bind = "127.0.0.1:8000"
workers = 2
timeout = 120
accesslog = "-"
errorlog = "-"
```

以后启动命令可以简化为：

```bash
gunicorn -c gunicorn.conf.py stadium_booking.wsgi:application
```

---

## 第六步：配置 Nginx

### 6.1 创建 Nginx 配置文件

```bash
sudo nano /etc/nginx/sites-available/stadium-booking
```

### 6.2 粘贴以下内容

```nginx
server {
    listen 80;
    server_name _;

    location /static/ {
        alias /home/你的用户名/StaduimBookingSystem/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**重要**：将 `你的用户名` 替换为实际的用户名（如 `ubuntu`）

### 6.3 启用配置

```bash
# 删除默认配置
sudo rm /etc/nginx/sites-enabled/default

# 启用新配置
sudo ln -s /etc/nginx/sites-available/stadium-booking /etc/nginx/sites-enabled/
```

### 6.4 测试配置

```bash
sudo nginx -t
```

如果显示以下内容，说明配置正确：

```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 6.5 重启 Nginx

```bash
sudo systemctl restart nginx
```

### 6.6 验证

在浏览器访问 `http://服务器IP`（不带端口号），应该能看到网站。

---

## 第七步：配置 Systemd 服务

配置服务后，Gunicorn 可以开机自启，并在崩溃时自动重启。

### 7.1 创建服务文件

```bash
sudo nano /etc/systemd/system/stadium-booking.service
```

### 7.2 粘贴以下内容

```ini
[Unit]
Description=Stadium Booking System
After=network.target

[Service]
User=你的用户名
Group=www-data
WorkingDirectory=/home/你的用户名/StaduimBookingSystem
Environment="PATH=/home/你的用户名/StaduimBookingSystem/venv/bin"
ExecStart=/home/你的用户名/StaduimBookingSystem/venv/bin/gunicorn --bind 127.0.0.1:8000 stadium_booking.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

**重要**：将 `你的用户名` 替换为实际的用户名

### 7.3 重新加载 systemd

```bash
sudo systemctl daemon-reload
```

### 7.4 启动服务

```bash
# 启动 Gunicorn
sudo systemctl start stadium-booking

# 设置开机自启
sudo systemctl enable stadium-booking
```

### 7.5 查看服务状态

```bash
sudo systemctl status stadium-booking
```

如果显示 `active (running)`，说明服务运行正常。

### 7.6 重启服务

```bash
sudo systemctl restart stadium-booking
```

---

## 第八步：配置防火墙

### 8.1 安装防火墙（如果未安装）

```bash
sudo apt install -y ufw
```

### 8.2 配置规则

```bash
# 开放 SSH（必须，否则会断开连接）
sudo ufw allow 22/tcp

# 开放 HTTP
sudo ufw allow 80/tcp

# 开放 HTTPS（备用）
sudo ufw allow 443/tcp
```

### 8.3 启用防火墙

```bash
sudo ufw enable
```

### 8.4 检查状态

```bash
sudo ufw status
```

---

## 常见问题

### 问题1：502 Bad Gateway

**原因**：Gunicorn 没有运行

**解决**：

```bash
# 启动 Gunicorn 服务
sudo systemctl start stadium-booking

# 检查状态
sudo systemctl status stadium-booking
```

### 问题2：403 Forbidden

**原因**：staticfiles 目录不存在或权限问题

**解决**：

```bash
cd ~/StaduimBookingSystem
source venv/bin/activate
python manage.py collectstatic --noinput

# 设置权限
chmod -R 755 ~/StaduimBookingSystem
```

### 问题3：连接被拒绝

**原因**：防火墙阻止或服务未启动

**解决**：

```bash
# 检查防火墙
sudo ufw status

# 开放端口
sudo ufw allow 80/tcp

# 检查服务状态
sudo systemctl status nginx
sudo systemctl status stadium-booking
```

### 问题4：静态文件不显示

**原因**：Nginx 配置中路径错误

**解决**：

1. 确认 staticfiles 目录存在：

```bash
ls -la ~/StaduimBookingSystem/staticfiles/
```

2. 检查 Nginx 配置中的路径是否正确：

```bash
sudo nano /etc/nginx/sites-available/stadium-booking
```

确保 `alias` 后面的路径与实际路径一致。

### 问题5：Gunicorn 启动失败

**原因**：端口被占用或配置错误

**解决**：

```bash
# 检查端口占用
sudo netstat -tlnp | grep 8000

# 如果有其他进程占用，停止它
sudo kill <进程ID>

# 重新启动 Gunicorn
sudo systemctl restart stadium-booking
```

### 问题6：网页显示 "Not Found"

**原因**：Nginx 配置中 `proxy_pass` 地址错误

**解决**：

确保 Nginx 配置中 `proxy_pass` 是 `http://127.0.0.1:8000`，而不是其他地址。

### 问题7：修改代码后不生效

**原因**：Gunicorn 没有重载

**解决**：

```bash
sudo systemctl restart stadium-booking
```

---

## 快速检查清单

部署完成后，使用以下清单确认一切正常：

| 检查项          | 命令                                      | 预期结果             |
| --------------- | ----------------------------------------- | -------------------- |
| Nginx 运行中    | `sudo systemctl status nginx`           | `active (running)` |
| Gunicorn 运行中 | `sudo systemctl status stadium-booking` | `active (running)` |
| 端口 8000 监听  | `sudo netstat -tlnp \| grep 8000`        | 显示 127.0.0.1:8000  |
| HTTP 访问       | `curl http://localhost`                 | 返回 HTML 内容       |
| 静态文件访问    | `curl http://localhost/static/`         | 显示文件列表或无权限 |
| 防火墙状态      | `sudo ufw status`                       | 80 端口开放          |

---

## 完整部署流程（快速参考）

```bash
# 1. 安装软件
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx git sqlite3

# 2. 上传项目文件
mkdir -p ~/StaduimBookingSystem
# 使用 scp/git 方式上传文件

# 3. 配置虚拟环境
cd ~/StaduimBookingSystem
python3 -m venv venv
source venv/bin/activate
pip install django gunicorn

# 4. 配置 Django
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput

# 启动gunicorn
gunicorn --bind 0.0.0.0:8000 stadium_booking.wsgi:application

# 5. 配置 Nginx
sudo nano /etc/nginx/sites-available/stadium-booking
# 粘贴配置内容
sudo rm /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/stadium-booking /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 6. 配置服务
sudo nano /etc/systemd/system/stadium-booking.service
# 粘贴服务内容
sudo systemctl daemon-reload
sudo systemctl start stadium-booking
sudo systemctl enable stadium-booking

# 7. 配置防火墙
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw enable
```

---

## 相关文件位置

| 文件          | 位置                                                   |
| ------------- | ------------------------------------------------------ |
| Django 项目   | `/home/用户名/StaduimBookingSystem/`                 |
| Nginx 配置    | `/etc/nginx/sites-available/stadium-booking`         |
| Systemd 服务  | `/etc/systemd/system/stadium-booking.service`        |
| Gunicorn 配置 | `/home/用户名/StaduimBookingSystem/gunicorn.conf.py` |
| Nginx 日志    | `/var/log/nginx/error.log`                           |
| Gunicorn 日志 | `journalctl -u stadium-booking`                      |
| 数据库        | `/home/用户名/StaduimBookingSystem/db.sqlite3`       |

---


---

## 附录：配置 DuckDNS 动态域名和 SSL 证书

### 第一步：注册 DuckDNS

1. 访问 https://www.duckdns.org/
2. 使用 Google/GitHub/Reddit 账号登录
3. 在 "domains" 区域输入你想要的子域名（如 `staduimbookingsystem`）
4. 点击 "add domain"
5. 复制页面顶部的 Token，保存备用

### 第二步：创建 DuckDNS 更新脚本

```bash
mkdir -p ~/duckdns
nano ~/duckdns/update.sh
```

输入以下内容（替换为你的域名和token）：

```bash
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=staduimbookingsystem&token=你的token&ipv6=true" | curl -k -o ~/duckdns/duck.log -K -
```

保存退出，然后：

```bash
chmod 700 ~/duckdns/update.sh
```

### 第三步：手动测试更新

```bash
~/duckdns/update.sh
cat ~/duckdns/duck.log
```

应该返回 `OK`。

### 第四步：设置定时更新（每5分钟）

```bash
crontab -e
```

添加：

```
*/5 * * * * ~/duckdns/update.sh >/dev/null 2>&1
```

### 第五步：验证 DNS 解析

```bash
nslookup staduimbookingsystem.duckdns.org
```

### 第六步：安装 certbot 和 DuckDNS 插件

```bash
source ~/StaduimBookingSystem/django/bin/activate
pip install certbot certbot-dns-duckdns
```

### 第七步：创建 DNS 验证配置

```bash
mkdir -p ~/.secrets/certbot
chmod 700 ~/.secrets/certbot
nano ~/.secrets/certbot/duckdns.ini
```

输入：

```ini
dns_duckdns_token = 你的DuckDNS-token
```

保存退出，然后：

```bash
chmod 600 ~/.secrets/certbot/duckdns.ini
```

### 第八步：创建 certbot 工作目录

```bash
mkdir -p ~/.certbot/etc ~/.certbot/var ~/.certbot/log
chmod 755 ~/.certbot/etc ~/.certbot/var ~/.certbot/log
```

### 第九步：申请 SSL 证书

```bash
source ~/StaduimBookingSystem/django/bin/activate && certbot certonly --authenticator dns-duckdns --dns-duckdns-credentials ~/.secrets/certbot/duckdns.ini -d staduimbookingsystem.duckdns.org --preferred-challenges dns-01 --config-dir ~/.certbot/etc --work-dir ~/.certbot/var --logs-dir ~/.certbot/log
```

### 第十步：配置 Nginx SSL

编辑 Nginx 配置：

```bash
sudo nano /etc/nginx/sites-available/stadium-booking
```

```nginx
server {
    listen 8443 ssl;
    listen [::]:8443 ssl;
    server_name staduimbookingsystem.duckdns.org;

    ssl_certificate /home/pi/.certbot/etc/live/staduimbookingsystem.duckdns.org/fullchain.pem;
    ssl_certificate_key /home/pi/.certbot/etc/live/staduimbookingsystem.duckdns.org/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location /static/ {
        alias /home/pi/StaduimBookingSystem/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**重要**：将 `pi` 替换为你的实际用户名。

测试并重启：

```bash
sudo nginx -t
sudo systemctl restart nginx
```

### 第十一步：设置证书自动续期

```bash
sudo crontab -e
```

添加：

```
0 3 * * * source /home/pi/StaduimBookingSystem/django/bin/activate && certbot renew --authenticator dns-duckdns --dns-duckdns-credentials /home/pi/.secrets/certbot/duckdns.ini --config-dir /home/pi/.certbot/etc --work-dir /home/pi/.certbot/var --logs-dir /home/pi/.certbot/log --quiet && systemctl reload nginx
```

### 第十二步：路由器端口映射

1. 登录路由器管理页面（通常是 `192.168.1.1` 或 `192.168.0.1`）
2. 找到 "端口转发" / "NAT" / "虚拟服务器"
3. 添加规则：

| 设置项 | 值 |
|--------|-----|
| 规则名称 | Stadium Booking |
| 外部端口 | 8443 |
| 内部端口 | 8443 |
| 内部IP | 树莓派IP（如 `192.168.1.100`） |
| 协议 | TCP |

### 第十三步：测试外网访问

在**手机4G网络**或**非同一WiFi**的设备上访问：

```
https://staduimbookingsystem.duckdns.org:8443/
```


*文档版本：1.1*
*最后更新：2026-05-04*