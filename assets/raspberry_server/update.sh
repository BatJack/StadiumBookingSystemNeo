#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
VENV_PATH="$SCRIPT_DIR/django"
SETTINGS_MODULE="stadium_booking.settings_production"

echo "=========================================="
echo "Stadium Booking System 更新脚本"
echo "=========================================="

cd $PROJECT_DIR || { echo "错误: 无法进入项目目录"; exit 1; }

echo ""
echo "[1/6] 激活虚拟环境..."
source $VENV_PATH/bin/activate || { echo "错误: 虚拟环境激活失败"; exit 1; }

echo ""
echo "[2/6] 拉取最新代码..."
git pull || { echo "警告: git pull 失败，继续执行..."; }

echo ""
echo "[3/6] 更新依赖..."
pip install -r requirements.txt --quiet

echo ""
echo "[4/6] 数据库迁移..."
python manage.py migrate --settings=$SETTINGS_MODULE || { echo "警告: 迁移失败"; }

echo ""
echo "[5/6] 收集静态文件..."
python manage.py collectstatic --settings=$SETTINGS_MODULE --noinput || { echo "错误: 静态文件收集失败"; exit 1; }

echo ""
echo "[6/6] 重启服务..."
sudo systemctl restart stadium-booking && echo "  ✓ Stadium Booking Service 重启成功" || { echo "  ✗ Stadium Booking Service 重启失败"; }
sudo systemctl restart nginx && echo "  ✓ Nginx 重启成功" || { echo "  ✗ Nginx 重启失败"; }

echo ""
echo "=========================================="
echo "更新完成！"
echo "=========================================="
echo ""
echo "服务状态:"
sudo systemctl status stadium-booking --no-pager -l | head -3
sudo systemctl status nginx --no-pager -l | head -3
echo ""
echo "查看日志: sudo journalctl -u stadium-booking -f"
