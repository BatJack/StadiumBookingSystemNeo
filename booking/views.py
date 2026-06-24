from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.db import models
from datetime import datetime, timedelta, time
from .models import Court, CourtAvailability, Booking, Profile, Student, BookingStudent, CourtType


def is_admin_user(user):
    try:
        return user.profile.user_type in ('admin', 'super_admin')
    except Profile.DoesNotExist:
        return False

def is_super_admin_user(user):
    try:
        return user.profile.user_type == 'super_admin'
    except Profile.DoesNotExist:
        return False


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if is_admin_user(user):
                return redirect('admin_dashboard')
            return redirect('court_list')
        else:
            messages.error(request, '用户名或密码错误')
    return render(request, 'booking/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def court_list(request):
    courts = Court.objects.all()
    today = timezone.now().date()
    return render(request, 'booking/court_list.html', {
        'courts': courts,
        'today': today,
        'is_admin': is_admin_user(request.user)
    })


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(
        user=request.user,
        status='active'
    ).order_by('date', 'start_time')
    return render(request, 'booking/my_bookings.html', {'bookings': bookings})


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    if booking.user != request.user and not is_admin_user(request.user):
        messages.error(request, '您没有权限取消此预约')
        return redirect('my_bookings')
    
    booking.status = 'cancelled'
    booking.save()
    messages.success(request, '预约已取消')
    
    if is_admin_user(request.user):
        return redirect('admin_bookings')
    return redirect('my_bookings')


@login_required
def admin_dashboard(request):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    return render(request, 'booking/admin/admin_dashboard.html', {
        'is_super_admin': is_super_admin_user(request.user),
    })


@login_required
def training_dashboard(request):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    return render(request, 'booking/admin/training_dashboard.html')


@login_required
def admin_statistics(request):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    courts_count = Court.objects.count()
    bookings_count = Booking.objects.count()
    availabilities_count = CourtAvailability.objects.count()
    students_count = Student.objects.count()
    
    return render(request, 'booking/admin/admin_statistics.html', {
        'courts_count': courts_count,
        'bookings_count': bookings_count,
        'availabilities_count': availabilities_count,
        'students_count': students_count
    })


@login_required
def admin_court_list(request):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    courts = Court.objects.select_related('court_type').all()
    court_types = CourtType.objects.all()
    return render(request, 'booking/admin/admin_court_list.html', {'courts': courts, 'court_types': court_types})


@login_required
def admin_court_add(request):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    if request.method == 'POST':
        description = request.POST.get('description')
        court_type_id = request.POST.get('court_type')
        court_number = request.POST.get('court_number')
        building = request.POST.get('building', '')
        
        court_type = None
        if court_type_id:
            try:
                court_type = CourtType.objects.get(id=court_type_id)
            except CourtType.DoesNotExist:
                pass
        
        # court_number 转为整数
        court_number_int = None
        if court_number:
            try:
                court_number_int = int(court_number)
            except (ValueError, TypeError):
                pass
        
        Court.objects.create(
            description=description,
            court_type=court_type,
            court_number=court_number_int,
            building=building
        )
        messages.success(request, '场地添加成功')
        return redirect('admin_court_list')
    
    court_types = CourtType.objects.all()
    building_choices = Court.BUILDING_CHOICES
    court_number_choices = Court.COURT_NUMBER_CHOICES
    return render(request, 'booking/admin/admin_court_form.html', {
        'court_types': court_types,
        'building_choices': building_choices,
        'court_number_choices': court_number_choices
    })


@login_required
def admin_court_edit(request, court_id):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    court = get_object_or_404(Court, id=court_id)
    
    if request.method == 'POST':
        court.description = request.POST.get('description')
        court_type_id = request.POST.get('court_type')
        court_number = request.POST.get('court_number')
        court.building = request.POST.get('building', '')
        
        if court_type_id:
            try:
                court.court_type = CourtType.objects.get(id=court_type_id)
            except CourtType.DoesNotExist:
                court.court_type = None
        else:
            court.court_type = None
        
        # court_number 转为整数
        if court_number:
            try:
                court.court_number = int(court_number)
            except (ValueError, TypeError):
                court.court_number = None
        else:
            court.court_number = None
        
        court.save()
        messages.success(request, '场地更新成功')
        return redirect('admin_court_list')
    
    court_types = CourtType.objects.all()
    building_choices = Court.BUILDING_CHOICES
    court_number_choices = Court.COURT_NUMBER_CHOICES
    return render(request, 'booking/admin/admin_court_form.html', {
        'court': court,
        'court_types': court_types,
        'building_choices': building_choices,
        'court_number_choices': court_number_choices
    })


@login_required
def admin_court_delete(request, court_id):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    court = get_object_or_404(Court, id=court_id)
    court.delete()
    messages.success(request, '场地删除成功')
    return redirect('admin_court_list')


@login_required
def admin_court_batch_add(request):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    if request.method == 'POST':
        court_type_id = request.POST.get('court_type')
        building = request.POST.get('building', '')
        court_numbers_str = request.POST.get('court_numbers', '')
        description = request.POST.get('description', '')
        
        court_type = None
        if court_type_id:
            try:
                court_type = CourtType.objects.get(id=court_type_id)
            except CourtType.DoesNotExist:
                pass
        
        # Parse court numbers from comma-separated string
        court_numbers = [n.strip() for n in court_numbers_str.split(',') if n.strip()]
        
        created_count = 0
        for court_number in court_numbers:
            try:
                court_number_int = int(court_number)
                Court.objects.create(
                    description=description,
                    court_type=court_type,
                    court_number=court_number_int,
                    building=building
                )
                created_count += 1
            except (ValueError, TypeError):
                continue
        
        if created_count > 0:
            messages.success(request, f'成功添加 {created_count} 个场地')
        else:
            messages.warning(request, '未添加任何场地，请检查输入')
        return redirect('admin_court_list')
    
    court_types = CourtType.objects.all()
    building_choices = Court.BUILDING_CHOICES
    return render(request, 'booking/admin/admin_court_batch_add.html', {
        'court_types': court_types,
        'building_choices': building_choices
    })


@login_required
def admin_court_batch_delete(request):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    if request.method == 'POST':
        court_ids_str = request.POST.get('court_ids', '')
        court_ids = [id.strip() for id in court_ids_str.split(',') if id.strip()]
        
        if court_ids:
            # Filter to only valid integer IDs
            valid_ids = []
            for id_str in court_ids:
                try:
                    valid_ids.append(int(id_str))
                except (ValueError, TypeError):
                    continue
            
            if valid_ids:
                Court.objects.filter(id__in=valid_ids).delete()
                messages.success(request, f'成功删除 {len(valid_ids)} 个场地')
            else:
                messages.warning(request, '未选中有效的场地')
        else:
            messages.warning(request, '请选择要删除的场地')
        return redirect('admin_court_list')
    
    return redirect('admin_court_list')


@login_required
def admin_court_type_list(request):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    court_types = CourtType.objects.prefetch_related('courts').all()
    return render(request, 'booking/admin/admin_court_type_list.html', {'court_types': court_types})


@login_required
def admin_court_type_add(request):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            CourtType.objects.create(name=name)
            messages.success(request, '场地类型添加成功')
        return redirect('admin_court_type_list')
    
    return render(request, 'booking/admin/admin_court_type_form.html')


@login_required
def admin_court_type_edit(request, type_id):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    court_type = get_object_or_404(CourtType, id=type_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            court_type.name = name
            court_type.save()
            messages.success(request, '场地类型更新成功')
        return redirect('admin_court_type_list')
    
    return render(request, 'booking/admin/admin_court_type_form.html', {'court_type': court_type})


@login_required
def admin_court_type_delete(request, type_id):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    court_type = get_object_or_404(CourtType, id=type_id)
    if court_type.is_default:
        messages.error(request, '系统默认类型不能删除')
    else:
        court_type.delete()
        messages.success(request, '场地类型删除成功')
    return redirect('admin_court_type_list')


@login_required
def admin_availability_list(request):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    courts = Court.objects.all()
    today = timezone.now().date()
    
    availabilities = CourtAvailability.objects.filter(
        end_date__gte=today
    ).select_related('court').order_by('start_date', 'start_time')
    
    return render(request, 'booking/admin/admin_availability_list.html', {
        'availabilities': availabilities,
        'courts': courts,
    })


@login_required
def admin_availability_add(request):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    if request.method == 'POST':
        court_id = request.POST.get('court')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        
        try:
            court = Court.objects.get(id=court_id)
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            if start_date > end_date:
                messages.error(request, '结束日期必须大于等于开始日期')
                return render(request, 'booking/admin/admin_availability_form.html', {
                    'courts': Court.objects.all(),
                })
            
            if start_time >= end_time:
                messages.error(request, '结束时间必须大于开始时间')
                return render(request, 'booking/admin/admin_availability_form.html', {
                    'courts': Court.objects.all(),
                })
            
            # 检查该场地是否已有时间段记录
            existing = CourtAvailability.objects.filter(court=court).first()
            if existing:
                messages.error(request, f'该场地已有时间段记录，请先编辑或删除现有记录')
                return render(request, 'booking/admin/admin_availability_form.html', {
                    'courts': Court.objects.all(),
                })
            
            CourtAvailability.objects.create(
                court=court,
                start_date=start_date,
                end_date=end_date,
                start_time=start_time,
                end_time=end_time
            )
            
            messages.success(request, '可用时间段设置成功')
            return redirect('admin_availability_list')
            
        except ValueError:
            messages.error(request, '时间格式错误')
        except Court.DoesNotExist:
            messages.error(request, '场地不存在')
    
    return render(request, 'booking/admin/admin_availability_form.html', {
        'courts': Court.objects.all(),
    })


@login_required
def admin_availability_edit(request, availability_id):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    try:
        availability = CourtAvailability.objects.get(id=availability_id)
    except CourtAvailability.DoesNotExist:
        messages.error(request, '时间段记录不存在')
        return redirect('admin_availability_list')
    
    if request.method == 'POST':
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            if start_date > end_date:
                messages.error(request, '结束日期必须大于等于开始日期')
                return render(request, 'booking/admin/admin_availability_edit.html', {
                    'availability': availability,
                })
            
            if start_time >= end_time:
                messages.error(request, '结束时间必须大于开始时间')
                return render(request, 'booking/admin/admin_availability_edit.html', {
                    'availability': availability,
                })
            
            availability.start_date = start_date
            availability.end_date = end_date
            availability.start_time = start_time
            availability.end_time = end_time
            availability.save()
            
            messages.success(request, '可用时间段更新成功')
            return redirect('admin_availability_list')
            
        except ValueError:
            messages.error(request, '时间格式错误')
    
    return render(request, 'booking/admin/admin_availability_edit.html', {
        'availability': availability,
    })


@login_required
def admin_availability_delete(request, availability_id):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    try:
        availability = CourtAvailability.objects.get(id=availability_id)
        court = availability.court
        
        # 删除该时间段范围内的所有预约记录
        deleted_bookings = Booking.objects.filter(
            court=court,
            date__gte=availability.start_date,
            date__lte=availability.end_date,
            start_time__gte=availability.start_time,
            end_time__lte=availability.end_time
        ).delete()
        
        # 删除时间段记录
        availability.delete()
        
        if deleted_bookings[0] > 0:
            messages.success(request, f'时间段已删除，同时删除了 {deleted_bookings[0]} 条预约记录')
        else:
            messages.success(request, '时间段已删除')
    except CourtAvailability.DoesNotExist:
        messages.error(request, '时间段记录不存在')
    
    return redirect('admin_availability_list')


@login_required
def admin_bookings(request):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    bookings = Booking.objects.all().select_related('user', 'court').order_by('date', 'start_time')
    return render(request, 'booking/admin/admin_bookings.html', {'bookings': bookings})


@login_required
def admin_booking_add(request):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        court_id = request.POST.get('court')
        date_str = request.POST.get('date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        booker_name = request.POST.get('booker_name')
        booker_phone = request.POST.get('booker_phone')
        
        try:
            user = User.objects.get(username=username)
            court = Court.objects.get(id=court_id)
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            if start_time >= end_time:
                messages.error(request, '结束时间必须大于开始时间')
                return render(request, 'booking/admin/admin_booking_form.html', {
                    'courts': Court.objects.all(),
                    'users': User.objects.all(),
                })
            
            if start_time.minute not in [0, 30] or end_time.minute not in [0, 30]:
                messages.error(request, '时间必须是整点或半点')
                return render(request, 'booking/admin/admin_booking_form.html', {
                    'courts': Court.objects.all(),
                    'users': User.objects.all(),
                })
            
            availability = CourtAvailability.objects.filter(
                court=court,
                start_date__lte=booking_date,
                end_date__gte=booking_date
            ).first()
            
            if not availability:
                messages.error(request, '该日期场地未开放预约')
                return render(request, 'booking/admin/admin_booking_form.html', {
                    'courts': Court.objects.all(),
                    'users': User.objects.all(),
                })
            
            if start_time < availability.start_time or end_time > availability.end_time:
                messages.error(request, '预约时间不在场地开放时间内')
                return render(request, 'booking/admin/admin_booking_form.html', {
                    'courts': Court.objects.all(),
                    'users': User.objects.all(),
                })
            
            conflicting_bookings = Booking.objects.filter(
                court=court,
                date=booking_date,
                status='active'
            ).exclude(
                end_time__lte=start_time
            ).exclude(
                start_time__gte=end_time
            )
            
            if conflicting_bookings.exists():
                messages.error(request, '该时间段已被预约')
                return render(request, 'booking/admin/admin_booking_form.html', {
                    'courts': Court.objects.all(),
                    'users': User.objects.all(),
                })
            
            Booking.objects.create(
                user=user,
                court=court,
                date=booking_date,
                start_time=start_time,
                end_time=end_time,
                booker_name=booker_name,
                booker_phone=booker_phone,
                status='active'
            )
            
            messages.success(request, '预约添加成功')
            return redirect('admin_bookings')
            
        except User.DoesNotExist:
            messages.error(request, '用户不存在')
        except Court.DoesNotExist:
            messages.error(request, '场地不存在')
        except ValueError:
            messages.error(request, '时间格式错误')
    
    return render(request, 'booking/admin/admin_booking_form.html', {
        'courts': Court.objects.all(),
        'users': User.objects.all(),
    })


@login_required
def admin_booking_edit(request, booking_id):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    booking = get_object_or_404(Booking, id=booking_id, booking_type='court')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'cancel':
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, '预约已取消')
            return redirect('admin_bookings')
        
        if action == 'delete':
            booking.delete()
            messages.success(request, '预约已删除')
            return redirect('admin_bookings')
    
    return render(request, 'booking/admin/admin_booking_edit.html', {'booking': booking})


@login_required
@require_GET
def get_time_slots(request):
    date_str = request.GET.get('date')
    court_id = request.GET.get('court_id')

    if not date_str:
        return JsonResponse({'error': '缺少日期参数'}, status=400)

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': '日期格式错误'}, status=400)

    courts = Court.objects.select_related('court_type').all()
    if court_id:
        courts = courts.filter(id=court_id)

    # 批量查 availability — 一次查询，按 court_id 分组
    avail_qs = CourtAvailability.objects.filter(
        start_date__lte=selected_date,
        end_date__gte=selected_date
    )
    avail_map = {a.court_id: a for a in avail_qs}

    # 批量查 bookings — 一次查询，按 court_id 分组，含课程预约学生信息
    all_bookings = Booking.objects.filter(
        court__in=[c.id for c in courts],
        date=selected_date,
        status='active'
    ).prefetch_related(
        models.Prefetch('students', queryset=BookingStudent.objects.select_related('student'))
    )

    bookings_by_court = {}
    for b in all_bookings:
        bookings_by_court.setdefault(b.court_id, []).append(b)

    data = []
    for court in courts:
        availability = avail_map.get(court.id)
        
        court_data = {
            'id': court.id,
            'name': court.name,
            'court_number': court.court_number,
            'court_type_name': court.court_type.name if court.court_type else None,
            'description': court.description,
            'is_available': availability is not None,
            'start_time': availability.start_time.strftime('%H:%M') if availability else None,
            'end_time': availability.end_time.strftime('%H:%M') if availability else None,
            'time_slots': []
        }
        
        if availability:
            bookings = bookings_by_court.get(court.id, [])

            booked_slots = {}
            for booking in bookings:
                current = datetime.combine(selected_date, booking.start_time)
                end_dt = datetime.combine(selected_date, booking.end_time)
                slot_info = {
                    'booking_type': booking.booking_type,
                    'booking_id': booking.id,
                    'booker_name': booking.booker_name,
                    'booker_phone': booking.booker_phone,
                }
                if booking.booking_type == 'course':
                    students = [
                        {'student__name': s.student.name, 'student__phone': s.student.phone, 'class_hours': s.class_hours}
                        for s in booking.students.all()
                    ]
                    slot_info['students'] = students
                    slot_info['student_count'] = len(students)
                    slot_info['total_class_hours'] = sum(s['class_hours'] for s in booking.students.all())
                while current < end_dt:
                    booked_slots[current.time()] = slot_info
                    current += timedelta(minutes=30)

            current_time = datetime.combine(selected_date, availability.start_time)
            end_time_dt = datetime.combine(selected_date, availability.end_time)

            while current_time < end_time_dt:
                slot_time = current_time.time()
                slot_end = (current_time + timedelta(minutes=30)).time()

                is_booked = slot_time in booked_slots
                booking_info = booked_slots.get(slot_time, None)

                slot_data = {
                    'start': slot_time.strftime('%H:%M'),
                    'end': slot_end.strftime('%H:%M'),
                    'label': f"{slot_time.strftime('%H:%M')}-{slot_end.strftime('%H:%M')}",
                    'is_booked': is_booked,
                }
                if booking_info:
                    slot_data['booking_type'] = booking_info['booking_type']
                    slot_data['booking_id'] = booking_info['booking_id']
                    slot_data['booker_name'] = booking_info['booker_name']
                    slot_data['booker_phone'] = booking_info['booker_phone']
                    if booking_info['booking_type'] == 'course':
                        slot_data['students'] = booking_info['students']
                        slot_data['student_count'] = booking_info['student_count']
                        slot_data['total_class_hours'] = booking_info['total_class_hours']

                court_data['time_slots'].append(slot_data)

                current_time += timedelta(minutes=30)
        
        data.append(court_data)

    now = timezone.localtime()
    return JsonResponse({
        'courts': data,
        'server_time': now.strftime('%Y-%m-%d %H:%M:%S'),
        'server_date': now.strftime('%Y-%m-%d'),
    })


@login_required
@require_POST
def create_booking_api(request):
    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的请求参数'}, status=400)
    
    court_id = data.get('court_id')
    date_str = data.get('date')
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')
    booker_name = data.get('booker_name')
    booker_phone = data.get('booker_phone')
    
    if not all([court_id, date_str, start_time_str, end_time_str, booker_name, booker_phone]):
        return JsonResponse({'error': '缺少必要参数'}, status=400)
    
    try:
        court = Court.objects.get(id=court_id)
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
    except (Court.DoesNotExist, ValueError):
        return JsonResponse({'error': '参数错误'}, status=400)
    
    if start_time >= end_time:
        return JsonResponse({'error': '结束时间必须大于开始时间'}, status=400)
    
    availability = CourtAvailability.objects.filter(
        court=court,
        start_date__lte=booking_date,
        end_date__gte=booking_date
    ).first()
    
    if not availability:
        return JsonResponse({'error': '该日期场地未开放预约'}, status=400)
    
    if start_time < availability.start_time or end_time > availability.end_time:
        return JsonResponse({'error': '预约时间不在场地开放时间内'}, status=400)
    
    conflicting_bookings = Booking.objects.filter(
        court=court,
        date=booking_date,
        status='active'
    ).exclude(
        end_time__lte=start_time
    ).exclude(
        start_time__gte=end_time
    )
    
    if conflicting_bookings.exists():
        return JsonResponse({'error': '该时间段已被预约'}, status=400)
    
    Booking.objects.create(
        user=request.user,
        court=court,
        date=booking_date,
        start_time=start_time,
        end_time=end_time,
        booker_name=booker_name,
        booker_phone=booker_phone,
        status='active'
    )
    
    return JsonResponse({'success': True, 'message': '预约成功'})


@login_required
def admin_student_list(request):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    students = Student.objects.all().order_by('name')
    return render(request, 'booking/admin/admin_student_list.html', {'students': students})


@login_required
def admin_student_add(request):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        total_class_hours = int(request.POST.get('total_class_hours', 0))
        
        Student.objects.create(name=name, phone=phone, total_class_hours=total_class_hours)
        messages.success(request, '学员添加成功')
        return redirect('admin_student_list')
    
    return render(request, 'booking/admin/admin_student_form.html')


@login_required
def admin_student_edit(request, student_id):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        student.name = request.POST.get('name')
        student.phone = request.POST.get('phone')
        student.total_class_hours = int(request.POST.get('total_class_hours', 0))
        student.save()
        messages.success(request, '学员信息更新成功')
        return redirect('admin_student_list')
    
    return render(request, 'booking/admin/admin_student_form.html', {'student': student})


@login_required
def admin_student_delete(request, student_id):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    student = get_object_or_404(Student, id=student_id)
    student.delete()
    messages.success(request, '学员删除成功')
    return redirect('admin_student_list')


@login_required
def admin_course_booking_list(request):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    today = timezone.now().date()
    bookings = Booking.objects.filter(booking_type='course').select_related('court').order_by('-date', 'start_time')
    return render(request, 'booking/admin/admin_course_booking_list.html', {
        'bookings': bookings,
        'today': today,
    })


@login_required
def admin_course_booking_add(request):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_booking':
            court_id = request.POST.get('court')
            date_str = request.POST.get('date')
            start_time_str = request.POST.get('start_time')
            end_time_str = request.POST.get('end_time')
            
            try:
                court = Court.objects.get(id=court_id)
                booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
                end_time = datetime.strptime(end_time_str, '%H:%M').time()
                
                if start_time >= end_time:
                    messages.error(request, '结束时间必须大于开始时间')
                    return render(request, 'booking/admin/admin_course_booking_form.html', {
                        'courts': Court.objects.all(),
                        'students': Student.objects.all(),
                    })
                
                if start_time.minute not in [0, 30] or end_time.minute not in [0, 30]:
                    messages.error(request, '时间必须是整点或半点')
                    return render(request, 'booking/admin/admin_course_booking_form.html', {
                        'courts': Court.objects.all(),
                        'students': Student.objects.all(),
                    })
                
                availability = CourtAvailability.objects.filter(
                    court=court,
                    start_date__lte=booking_date,
                    end_date__gte=booking_date
                ).first()
                
                if not availability:
                    messages.error(request, '该日期场地未开放预约')
                    return render(request, 'booking/admin/admin_course_booking_form.html', {
                        'courts': Court.objects.all(),
                        'students': Student.objects.all(),
                    })
                
                if start_time < availability.start_time or end_time > availability.end_time:
                    messages.error(request, '预约时间不在场地开放时间内')
                    return render(request, 'booking/admin/admin_course_booking_form.html', {
                        'courts': Court.objects.all(),
                        'students': Student.objects.all(),
                    })
                
                conflicting = Booking.objects.filter(
                    court=court,
                    date=booking_date,
                    status='active'
                ).exclude(
                    end_time__lte=start_time
                ).exclude(
                    start_time__gte=end_time
                )
                
                if conflicting.exists():
                    messages.error(request, '该时间段已被预约')
                    return render(request, 'booking/admin/admin_course_booking_form.html', {
                        'courts': Court.objects.all(),
                        'students': Student.objects.all(),
                    })
                
                booking = Booking.objects.create(
                    booking_type='course',
                    court=court,
                    date=booking_date,
                    start_time=start_time,
                    end_time=end_time,
                    status='active'
                )
                
                messages.success(request, '课程预约已创建，请添加学生')
                return redirect('admin_course_booking_edit', booking_id=booking.id)
                
            except Court.DoesNotExist:
                messages.error(request, '场地不存在')
            except ValueError:
                messages.error(request, '时间格式错误')
        
        elif action == 'add_students':
            booking_id = request.POST.get('booking_id')
            booking = get_object_or_404(Booking, id=booking_id, booking_type='course')
            
            student_ids = request.POST.getlist('students')
            class_hours = request.POST.get('class_hours')
            
            if not student_ids:
                messages.error(request, '请至少选择一名学员')
                return render(request, 'booking/admin/admin_course_booking_edit.html', {
                    'booking': booking,
                    'students': Student.objects.all(),
                })
            
            try:
                hours = int(class_hours)
                if hours <= 0:
                    messages.error(request, '课时数必须大于0')
                    return render(request, 'booking/admin/admin_course_booking_edit.html', {
                        'booking': booking,
                        'students': Student.objects.all(),
                    })
            except (ValueError, TypeError):
                messages.error(request, '课时数格式错误')
                return render(request, 'booking/admin/admin_course_booking_edit.html', {
                    'booking': booking,
                    'students': Student.objects.all(),
                })
            
            added = 0
            for sid in student_ids:
                try:
                    student = Student.objects.get(id=sid)
                    
                    if booking.students.filter(student=student).exists():
                        messages.warning(request, f'学员 {student.name} 已在课程预约中')
                        continue
                    
                    if student.total_class_hours < hours:
                        messages.warning(request, f'学员 {student.name} 课时不足（当前{student.total_class_hours}课时）')
                        continue
                    
                    student.total_class_hours -= hours
                    student.save()
                    
                    BookingStudent.objects.create(
                        booking=booking,
                        student=student,
                        class_hours=hours
                    )
                    added += 1
                except Student.DoesNotExist:
                    pass
            
            if added > 0:
                messages.success(request, f'成功添加 {added} 名学员，已扣除课时 {hours}')
            return redirect('admin_course_booking_edit', booking_id=booking_id)
    
    return render(request, 'booking/admin/admin_course_booking_form.html', {
        'courts': Court.objects.all(),
        'students': Student.objects.all(),
    })


@login_required
def admin_course_booking_edit(request, booking_id):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    booking = get_object_or_404(Booking, id=booking_id, booking_type='course')
    booking_students = booking.students.select_related('student').all()
    all_students = Student.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'remove_student':
            cs_id = request.POST.get('cs_id')
            try:
                cs = BookingStudent.objects.get(id=cs_id, booking=booking)
                student = cs.student
                hours = cs.class_hours
                
                student.total_class_hours += hours
                student.save()
                
                cs.delete()
                messages.success(request, f'已移除学员 {student.name}，退 {hours} 课时')
            except BookingStudent.DoesNotExist:
                messages.error(request, '操作失败')
        
        elif action == 'add_students':
            student_ids = request.POST.getlist('students')
            class_hours = request.POST.get('class_hours')
            
            if not student_ids:
                messages.error(request, '请至少选择一名学员')
                return render(request, 'booking/admin/admin_course_booking_edit.html', {
                    'booking': booking,
                    'booking_students': booking_students,
                    'students': all_students,
                })
            
            try:
                hours = int(class_hours)
                if hours <= 0:
                    messages.error(request, '课时数必须大于0')
                    return render(request, 'booking/admin/admin_course_booking_edit.html', {
                        'booking': booking,
                        'booking_students': booking_students,
                        'students': all_students,
                    })
            except (ValueError, TypeError):
                messages.error(request, '课时数格式错误')
                return render(request, 'booking/admin/admin_course_booking_edit.html', {
                    'booking': booking,
                    'booking_students': booking_students,
                    'students': all_students,
                })
            
            added = 0
            for sid in student_ids:
                try:
                    student = Student.objects.get(id=sid)
                    
                    if booking.students.filter(student=student).exists():
                        messages.warning(request, f'学员 {student.name} 已在课程预约中')
                        continue
                    
                    if student.total_class_hours < hours:
                        messages.warning(request, f'学员 {student.name} 课时不足（当前{student.total_class_hours}课时）')
                        continue
                    
                    student.total_class_hours -= hours
                    student.save()
                    
                    BookingStudent.objects.create(
                        booking=booking,
                        student=student,
                        class_hours=hours
                    )
                    added += 1
                except Student.DoesNotExist:
                    pass
            
            if added > 0:
                messages.success(request, f'成功添加 {added} 名学员，已扣除课时 {hours}')
            return redirect('admin_course_booking_edit', booking_id=booking_id)
        
        elif action == 'cancel_booking':
            if booking.status == 'active':
                for cs in booking.students.all():
                    cs.student.total_class_hours += cs.class_hours
                    cs.student.save()
                    cs.delete()
                booking.status = 'cancelled'
                booking.save()
                messages.success(request, '课程预约已取消，所有学员课时已退回')
            return redirect('admin_course_booking_list')
        
        elif action == 'update_booking':
            date_str = request.POST.get('date')
            start_time_str = request.POST.get('start_time')
            end_time_str = request.POST.get('end_time')
            
            try:
                booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
                end_time = datetime.strptime(end_time_str, '%H:%M').time()
                
                if start_time >= end_time:
                    messages.error(request, '结束时间必须大于开始时间')
                    return render(request, 'booking/admin/admin_course_booking_edit.html', {
                        'booking': booking,
                        'booking_students': booking_students,
                        'students': all_students,
                    })
                
                booking.date = booking_date
                booking.start_time = start_time
                booking.end_time = end_time
                booking.save()
                messages.success(request, '课程预约信息已更新')
            except ValueError:
                messages.error(request, '时间格式错误')
            
            return redirect('admin_course_booking_edit', booking_id=booking_id)
    
    return render(request, 'booking/admin/admin_course_booking_edit.html', {
        'booking': booking,
        'booking_students': booking_students,
        'students': all_students,
    })


@login_required
def admin_course_booking_delete(request, booking_id):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    booking = get_object_or_404(Booking, id=booking_id, booking_type='course')
    
    if booking.status == 'active':
        for cs in booking.students.all():
            cs.student.total_class_hours += cs.class_hours
            cs.student.save()
            cs.delete()
    
    booking.delete()
    messages.success(request, '课程预约已删除')
    return redirect('admin_course_booking_list')


@login_required
def admin_user_list(request):
    if not is_super_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('admin_dashboard')
    
    users = User.objects.select_related('profile').all().order_by('username')
    return render(request, 'booking/admin/admin_user_list.html', {'users': users})


@login_required
def admin_user_edit(request, user_id):
    if not is_super_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('admin_dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        new_user_type = request.POST.get('user_type')
        email = request.POST.get('email')
        
        if new_user_type not in dict(Profile.USER_TYPE_CHOICES):
            messages.error(request, '无效的用户类型')
            return redirect('admin_user_edit', user_id=user_id)
        
        # 不允许超级管理员把自己降级
        if user == request.user and new_user_type != 'super_admin':
            messages.error(request, '不能修改自己的用户类型')
            return redirect('admin_user_edit', user_id=user_id)
        
        user.email = email
        user.save()
        
        profile = user.profile
        profile.user_type = new_user_type
        profile.save()
        
        messages.success(request, f'用户 "{user.username}" 信息已更新')
        return redirect('admin_user_list')
    
    return render(request, 'booking/admin/admin_user_edit.html', {'edit_user': user})


@login_required
def admin_user_delete(request, user_id):
    if not is_super_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('admin_dashboard')
    
    if request.user.id == user_id:
        messages.error(request, '不能删除自己的账号')
        return redirect('admin_user_list')
    
    user = get_object_or_404(User, id=user_id)
    username = user.username
    user.delete()
    messages.success(request, f'用户 "{username}" 已删除')
    return redirect('admin_user_list')
