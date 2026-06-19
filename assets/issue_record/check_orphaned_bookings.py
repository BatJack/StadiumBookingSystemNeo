import os
import sys

# 设置输出编码为UTF-8
sys.stdout.reconfigure(encoding='utf-8')

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stadium_booking.settings')
django.setup()

from booking.models import Booking, Court, CourtAvailability, BookingStudent
from django.db import connection

def check_orphaned_bookings():
    """检查孤立的预约记录"""
    print("=" * 60)
    print("检查数据库中的孤立预约记录")
    print("=" * 60)
    
    # 1. 检查关联到不存在场地的预约
    print("\n1. 检查关联到不存在场地的预约...")
    orphaned_by_court = Booking.objects.exclude(court__in=Court.objects.all())
    if orphaned_by_court.exists():
        print(f"   [警告] 发现 {orphaned_by_court.count()} 条预约关联到不存在的场地:")
        for booking in orphaned_by_court:
            print(f"      - 预约ID: {booking.id}, 场地ID: {booking.court_id}, 日期: {booking.date}")
    else:
        print("   [正常] 没有发现关联到不存在场地的预约")
    
    # 2. 检查关联到不存在用户的预约（允许user为null）
    print("\n2. 检查关联到不存在用户的预约...")
    from django.contrib.auth.models import User
    orphaned_by_user = Booking.objects.exclude(user__in=User.objects.all()).exclude(user__isnull=True)
    if orphaned_by_user.exists():
        print(f"   [警告] 发现 {orphaned_by_user.count()} 条预约关联到不存在的用户:")
        for booking in orphaned_by_user:
            print(f"      - 预约ID: {booking.id}, 用户ID: {booking.user_id}")
    else:
        print("   [正常] 没有发现关联到不存在用户的预约")
    
    # 3. 检查关联到不存在预约的学员记录
    print("\n3. 检查关联到不存在预约的学员记录...")
    orphaned_booking_students = BookingStudent.objects.exclude(booking__in=Booking.objects.all())
    if orphaned_booking_students.exists():
        print(f"   [警告] 发现 {orphaned_booking_students.count()} 条学员记录关联到不存在的预约:")
        for bs in orphaned_booking_students:
            print(f"      - 记录ID: {bs.id}, 预约ID: {bs.booking_id}, 学员: {bs.student.name}")
    else:
        print("   [正常] 没有发现关联到不存在预约的学员记录")
    
    # 4. 检查关联到不存在学员的预约学员记录
    print("\n4. 检查关联到不存在学员的预约学员记录...")
    from booking.models import Student
    orphaned_students = BookingStudent.objects.exclude(student__in=Student.objects.all())
    if orphaned_students.exists():
        print(f"   [警告] 发现 {orphaned_students.count()} 条学员记录关联到不存在的学员:")
        for bs in orphaned_students:
            print(f"      - 记录ID: {bs.id}, 学员ID: {bs.student_id}, 预约: {bs.booking}")
    else:
        print("   [正常] 没有发现关联到不存在学员的学员记录")
    
    # 5. 检查关联到不存在场地的可用时间段
    print("\n5. 检查关联到不存在场地的可用时间段...")
    orphaned_availabilities = CourtAvailability.objects.exclude(court__in=Court.objects.all())
    if orphaned_availabilities.exists():
        print(f"   [警告] 发现 {orphaned_availabilities.count()} 条可用时间段关联到不存在的场地:")
        for avail in orphaned_availabilities:
            print(f"      - 时间段ID: {avail.id}, 场地ID: {avail.court_id}, 日期: {avail.start_date} 至 {avail.end_date}")
    else:
        print("   [正常] 没有发现关联到不存在场地的可用时间段")
    
    # 6. 检查状态为cancelled但仍显示为active的预约
    print("\n6. 检查预约状态统计...")
    total_bookings = Booking.objects.count()
    active_bookings = Booking.objects.filter(status='active').count()
    cancelled_bookings = Booking.objects.filter(status='cancelled').count()
    print(f"   总预约数: {total_bookings}")
    print(f"   有效预约: {active_bookings}")
    print(f"   已取消预约: {cancelled_bookings}")
    
    # 7. 检查是否有已取消的预约仍有关联的学员记录
    print("\n7. 检查已取消预约的学员记录...")
    cancelled_with_students = Booking.objects.filter(status='cancelled').filter(students__isnull=False).distinct()
    if cancelled_with_students.exists():
        print(f"   [警告] 发现 {cancelled_with_students.count()} 条已取消预约仍有关联学员记录:")
        for booking in cancelled_with_students:
            student_count = booking.students.count()
            print(f"      - 预约ID: {booking.id}, 关联学员数: {student_count}")
    else:
        print("   [正常] 已取消预约没有关联学员记录")
    
    # 8. 使用原始SQL检查外键约束问题
    print("\n8. 使用SQL检查外键引用完整性...")
    with connection.cursor() as cursor:
        # 检查booking表中court_id是否在court表中存在
        cursor.execute("""
            SELECT b.id, b.court_id 
            FROM booking_booking b 
            LEFT JOIN booking_court c ON b.court_id = c.id 
            WHERE c.id IS NULL
        """)
        orphaned = cursor.fetchall()
        if orphaned:
            print(f"   [警告] 发现 {len(orphaned)} 条预约引用了不存在的场地ID:")
            for row in orphaned:
                print(f"      - 预约ID: {row[0]}, 场地ID: {row[1]}")
        else:
            print("   [正常] 所有预约的场地引用都有效")
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)

if __name__ == '__main__':
    check_orphaned_bookings()
