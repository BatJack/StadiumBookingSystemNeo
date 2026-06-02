from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from datetime import datetime, timedelta, time
from .models import Court, CourtAvailability, Booking, Profile, Student, BookingStudent, CourtType
import socket
import struct


def get_network_time():
    try:
        ntp_servers = ['ntp.aliyun.com', 'ntp.tencent.com']
        for server in ntp_servers:
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                client.settimeout(1)
                data = b'\x1b' + 47 * b'\x00'
                client.sendto(data, (server, 123))
                response, _ = client.recvfrom(1024)
                client.close()
                
                if response:
                    unpacked = struct.unpack('!12I', response[:48])
                    timestamp = unpacked[10] - 2208988800
                    return datetime.fromtimestamp(timestamp, tz=timezone.get_current_timezone())
            except Exception:
                continue
    except Exception:
        pass
    return None


def get_current_time():
    network_time = get_network_time()
    if network_time:
        return network_time
    return timezone.now()


def is_admin_user(user):
    try:
        return user.profile.user_type == 'admin'
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
    
    return render(request, 'booking/admin/admin_dashboard.html')


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
        name = request.POST.get('name')
        description = request.POST.get('description')
        court_type_id = request.POST.get('court_type')
        court_number = request.POST.get('court_number', '')
        
        court_type = None
        if court_type_id:
            try:
                court_type = CourtType.objects.get(id=court_type_id)
            except CourtType.DoesNotExist:
                pass
        
        Court.objects.create(
            name=name,
            description=description,
            court_type=court_type,
            court_number=court_number
        )
        messages.success(request, '场地添加成功')
        return redirect('admin_court_list')
    
    court_types = CourtType.objects.all()
    return render(request, 'booking/admin/admin_court_form.html', {'court_types': court_types})


@login_required
def admin_court_edit(request, court_id):
    if not is_admin_user(request.user):
        messages.error(request, '您没有权限访问此页面')
        return redirect('court_list')
    
    court = get_object_or_404(Court, id=court_id)
    
    if request.method == 'POST':
        court.name = request.POST.get('name')
        court.description = request.POST.get('description')
        court_type_id = request.POST.get('court_type')
        court.court_number = request.POST.get('court_number', '')
        
        if court_type_id:
            try:
                court.court_type = CourtType.objects.get(id=court_type_id)
            except CourtType.DoesNotExist:
                court.court_type = None
        else:
            court.court_type = None
        
        court.save()
        messages.success(request, '场地更新成功')
        return redirect('admin_court_list')
    
    court_types = CourtType.objects.all()
    return render(request, 'booking/admin/admin_court_form.html', {'court': court, 'court_types': court_types})


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

    courts = Court.objects.all()
    if court_id:
        courts = courts.filter(id=court_id)
    data = []
    
    for court in courts:
        availability = CourtAvailability.objects.filter(
            court=court,
            start_date__lte=selected_date,
            end_date__gte=selected_date
        ).first()
        
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
            bookings = Booking.objects.filter(
                court=court,
                date=selected_date,
                status='active'
            )

            booked_slots = {}
            for booking in bookings:
                current = datetime.combine(selected_date, booking.start_time)
                end_dt = datetime.combine(selected_date, booking.end_time)
                while current < end_dt:
                    slot_info = {
                        'booking_type': booking.booking_type,
                        'booking_id': booking.id,
                        'booker_name': booking.booker_name,
                        'booker_phone': booking.booker_phone,
                    }
                    if booking.booking_type == 'course':
                        students = list(booking.students.select_related('student').values(
                            'student__name', 'student__phone', 'class_hours'
                        ))
                        slot_info['students'] = students
                        slot_info['student_count'] = len(students)
                        slot_info['total_class_hours'] = sum(s['class_hours'] for s in students)
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

    now = get_current_time()
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
