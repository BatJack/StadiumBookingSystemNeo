# 体育场馆预约系统 — 快速上手指南

## 一、环境准备

```bash
# 1. 安装 Python 3.10+
# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库
mkdir data
python manage.py migrate

# 4. 配置密钥（首次运行必做）
#    开发环境: 复制模板文件后直接使用
cp local_settings.py.example local_settings.py

#    生产环境: 设置环境变量
set DJANGO_SECRET_KEY=your-secret-key    # Windows
export DJANGO_SECRET_KEY=your-secret-key # Linux/Mac
```

> 生成密钥命令：`python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

---

## 二、创建用户

```bash
# 交互式创建（推荐）
python create_user_cli.py

# 或命令行创建
python create_user_cli.py -u admin -p 123456 --super-admin   # 超级管理员
python create_user_cli.py -u staff -p 123456 --admin          # 管理员
python create_user_cli.py -u user1 -p 123456                  # 普通用户
```

### 用户类型

| 类型       | 说明                            |
| ---------- | ------------------------------- |
| 普通用户   | 只能预约场地、查看自己的预约    |
| 管理员     | 可管理场地/时段/预约/学员/课程  |
| 超级管理员 | 管理员全部权限 + 可管理所有用户 |

---

## 三、启动系统

```bash
# 开发
python manage.py runserver

# 局域网访问
python manage.py runserver 0.0.0.0:8000

# 生产（gunicorn）
gunicorn --bind 0.0.0.0:8000 stadium_booking.wsgi:application
```

访问 http://127.0.0.1:8000/ 登录。

---

## 四、管理员首次配置

管理员登录后进入 **管理后台**，按顺序完成：

```
① 场地类型管理 → 添加场地类型（如"羽毛球场"）
② 场地管理 → 添加场地（选择类型、填写编号/名称）
③ 可用时间段 → 设置场地可预约的日期范围和开放时间
```

完成后普通用户即可在预约页面看到场地并进行预约。

---

## 五、常用命令速查

```bash
python manage.py runserver          # 启动开发服务器
python manage.py migrate            # 应用数据库迁移
python manage.py makemigrations     # 生成迁移文件（修改 models.py 后执行）
python manage.py test booking       # 运行测试
python manage.py clearsessions      # 清理过期会话
python manage.py collectstatic      # 收集静态文件（生产部署用）
```

---

## 六、生产部署要点

```bash
# 1. 设置环境变量
export DJANGO_SECRET_KEY='...'
export DJANGO_DEBUG=False
export DJANGO_ALLOWED_HOSTS=yourdomain.com

# 2. 收集静态文件
python manage.py collectstatic

# 3. 用 gunicorn 启动
gunicorn --bind 0.0.0.0:8000 -w 4 stadium_booking.wsgi:application

# 4. 或使用一键更新脚本
bash update.sh
```

### 安全提醒

- `settings_production.py` 启用了 HSTS、Secure Cookie 等安全头，**仅在生产环境使用**
- 数据库位于 `data/db.sqlite3`（已在 `.gitignore` 中），不会被提交到 Git
- 定期清理：`python manage.py clearsessions`（建议 cron 每日执行）
- 备份数据库：复制 `data/db.sqlite3` 文件即可

---

## 七、目录结构

```
├── stadium_booking/      # Django 项目配置
│   ├── settings.py       # 开发环境配置
│   ├── settings_production.py  # 生产环境配置
│   └── urls.py           # 根路由
├── booking/              # 主应用
│   ├── models.py         # 数据模型
│   ├── views.py          # 视图函数
│   ├── urls.py           # 路由
│   └── templates/        # 页面模板
├── data/                 # 数据库文件（已 gitignore）
├── create_user_cli.py    # 命令行创建用户
├── local_settings.py.example  # 密钥模板
└── update.sh             # 部署更新脚本
```
