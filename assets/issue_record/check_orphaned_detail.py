import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stadium_booking.settings')
django.setup()

from booking.models import Booking, CourtAvailability
from django.utils import timezone

today = timezone.now().date()

# 检查B馆篮球场5号的availability记录
from booking.models import Court
court = Court.objects.get(name='B馆篮球场5号')
print(f"场地: {court.name}")

availabilities = CourtAvailability.objects.filter(court=court)
print(f"\n该场地的时间段记录:")
for avail in availabilities:
    print(f"  {avail.start_date} 至 {avail.end_date}, 时间: {avail.start_time}-{avail.end_time}")

# 检查这3条孤立预约
orphaned_ids = [3, 4, 6]
print(f"\n孤立预约详情:")
for booking_id in orphaned_ids:
    booking = Booking.objects.get(id=booking_id)
    print(f"\n预约ID={booking.id}:")
    print(f"  日期: {booking.date}")
    print(f"  时间: {booking.start_time}-{booking.end_time}")
    print(f"  预约人: {booking.booker_name}")
    print(f"  电话: {booking.booker_phone}")
    
    # 检查是否有时间段覆盖该日期
    avail_for_date = CourtAvailability.objects.filter(
        court=booking.court,
        start_date__lte=booking.date,
        end_date__gte=booking.date
    )
    if avail_for_date.exists():
        print(f"  有时间段覆盖该日期:")
        for avail in avail_for_date:
            print(f"    {avail.start_date} 至 {avail.end_date}, 时间: {avail.start_time}-{avail.end_time}")
            print(f"    预约时间 {booking.start_time}-{booking.end_time} 是否在开放时间范围内: {booking.start_time >= avail.start_time and booking.end_time <= avail.end_time}")
    else:
        print(f"  无时间段覆盖该日期")
