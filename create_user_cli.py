#!/usr/bin/env python3
"""
命令行用户创建工具
用于在服务器上创建用户（无需GUI）

用法:
    python create_user_cli.py                    # 交互模式
    python create_user_cli.py -u username -p password [-e email] [--admin|--super-admin]
    python create_user_cli.py --username username --password password [--email email] [--admin|--super-admin]
"""

import os
import sys
import argparse


def setup_django():
    """初始化 Django 环境"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stadium_booking.settings')
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import django
    django.setup()


def create_user_cli(username, password, email='', user_type='regular'):
    """
    创建用户

    Args:
        username: 用户名
        password: 密码
        email: 邮箱（可选）
        user_type: 用户类型 ('super_admin', 'admin' 或 'regular')
    """
    from django.contrib.auth.models import User
    from booking.models import Profile

    try:
        # 检查用户是否已存在
        if User.objects.filter(username=username).exists():
            print(f"错误：用户 '{username}' 已存在")
            return False

        # 创建用户
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            is_staff=(user_type in ('admin', 'super_admin')),
            is_superuser=(user_type == 'super_admin')
        )

        # 创建 Profile
        Profile.objects.create(
            user=user,
            user_type=user_type
        )

        if user_type == 'super_admin':
            type_name = "超级管理员"
        elif user_type == 'admin':
            type_name = "管理员"
        else:
            type_name = "普通用户"
        print(f"\n✓ 用户创建成功！")
        print(f"  用户名: {username}")
        print(f"  邮箱: {email or '未设置'}")
        print(f"  类型: {type_name}")
        return True

    except Exception as e:
        print(f"错误：创建失败 - {str(e)}")
        return False


def interactive_mode():
    """交互模式"""
    print("\n" + "="*50)
    print("         体育场馆预约系统 - 创建用户")
    print("="*50)

    # 获取用户名
    while True:
        username = input("\n请输入用户名: ").strip()
        if username:
            break
        print("用户名不能为空")

    # 获取密码
    while True:
        password = input("请输入密码: ").strip()
        if not password:
            print("密码不能为空")
            continue
        if len(password) < 6:
            print("密码长度至少为6位")
            continue
        break

    # 获取邮箱（可选）
    email = input("请输入邮箱（可选，回车跳过）: ").strip()

    # 选择用户类型
    print("\n用户类型:")
    print("  1. 普通用户 - 可预约场地、查看预约")
    print("  2. 管理员 - 可管理场地、设置时间段、管理预约")
    print("  3. 超级管理员 - 拥有全部权限，可管理所有用户")

    while True:
        choice = input("\n请选择 (1/2/3): ").strip()
        if choice == '1':
            user_type = 'regular'
            break
        elif choice == '2':
            user_type = 'admin'
            break
        elif choice == '3':
            user_type = 'super_admin'
            break
        print("无效选择，请输入 1、2 或 3")

    # 确认信息
    print("\n" + "-"*50)
    print("确认信息:")
    print(f"  用户名: {username}")
    print(f"  密码: {'*' * len(password)}")
    print(f"  邮箱: {email or '未设置'}")
    type_display = {'super_admin': '超级管理员', 'admin': '管理员', 'regular': '普通用户'}.get(user_type, user_type)
    print(f"  类型: {type_display}")
    print("-"*50)

    confirm = input("\n确认创建? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return False

    return create_user_cli(username, password, email, user_type)


def main():
    parser = argparse.ArgumentParser(
        description='体育场馆预约系统 - 创建用户工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python create_user_cli.py                                    # 交互模式
    python create_user_cli.py -u test -p 123456                # 创建普通用户
    python create_user_cli.py -u admin -p 123456 --admin        # 创建管理员
    python create_user_cli.py -u user1 -p pass123 -e a@b.com   # 带邮箱的管理员
    python create_user_cli.py -u super -p 123456 --super-admin # 创建超级管理员
        """
    )

    parser.add_argument('-u', '--username', help='用户名')
    parser.add_argument('-p', '--password', help='密码')
    parser.add_argument('-e', '--email', default='', help='邮箱（可选）')
    parser.add_argument('--admin', action='store_true', help='创建为管理员')
    parser.add_argument('--super-admin', action='store_true', help='创建为超级管理员')

    args = parser.parse_args()

    # 初始化 Django
    setup_django()

    # 如果没有参数，进入交互模式
    if not args.username and not args.password:
        interactive_mode()
        return

    # 命令行模式
    if not args.username:
        print("错误：用户名不能为空")
        print("使用 --help 查看帮助")
        sys.exit(1)

    if not args.password:
        print("错误：密码不能为空")
        print("使用 --help 查看帮助")
        sys.exit(1)

    if len(args.password) < 6:
        print("错误：密码长度至少为6位")
        sys.exit(1)

    if args.super_admin:
        user_type = 'super_admin'
    elif args.admin:
        user_type = 'admin'
    else:
        user_type = 'regular'
    success = create_user_cli(args.username, args.password, args.email, user_type)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
