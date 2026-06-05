﻿from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, time, timedelta
from booking.models import Profile, CourtType, Court, CourtAvailability, Booking, Student, BookingStudent


class ModelTests(TestCase):
    """数据模型测试"""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        Profile.objects.create(user=self.admin_user, user_type='admin')

        self.regular_user = User.objects.create_user(
            username='user1',
            password='user123',
            email='user1@test.com'
        )
        Profile.objects.create(user=self.regular_user, user_type='regular')

        self.court_type, _ = CourtType.objects.get_or_create(
            name='羽毛球场',
            defaults={'is_default': False}
        )
        self.court = Court.objects.create(
            court_type=self.court_type,
            name='羽毛球场A',
            court_number='1'
        )
        self.availability = CourtAvailability.objects.create(
            court=self.court,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            start_time=time(9, 0),
            end_time=time(21, 0)
        )

    def test_profile_creation(self):
        """测试用户类型创建"""
        self.assertEqual(self.admin_user.profile.user_type, 'admin')
        self.assertEqual(self.regular_user.profile.user_type, 'regular')

    def test_court_str(self):
        """测试场地字符串表示""
        self.assertEqual(str(self.court), '羽毛球场 - 1')

    def test_availability_check(self):
        """测试时间段可用性检查""
        self.assertTrue(self.availability.is_date_available(date.today()))
        self.assertFalse(self.availability.is_date_available(date.today() - timedelta(days=10)))

    def test_booking_creation(self):
        """测试预约创建"""
        booking = Booking.objects.create(
            user=self.regular_user,
            court=self.court,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(11, 0),
            booker_name='测试用户',
            booker_phone='13800138000'
        )
        self.assertEqual(booking.status, 'active')
        self.assertTrue(booking.is_court_booking())

    def test_student_creation(self):
        """测试学员创建"""
        student = Student.objects.create(
            name='张三',
            phone='13900139000',
            total_class_hours=20
        )
        self.assertEqual(student.total_class_hours, 20)

    def test_booking_student(self):
        """测试预约学员关联"""
        student = Student.objects.create(name='李四', phone='13900139001', total_class_hours=10)
        booking = Booking.objects.create(
            booking_type='course',
            court=self.court,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(11, 0)
        )
        BookingStudent.objects.create(booking=booking, student=student, class_hours=2)
        self.assertEqual(booking.get_student_count(), 1)
        self.assertEqual(booking.get_total_class_hours(), 2)


class AuthenticationTests(TestCase):
    """用户认证测试"""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123'
        )
        Profile.objects.create(user=self.admin_user, user_type='admin')

        self.regular_user = User.objects.create_user(
            username='user1',
            password='user123'
        )
        Profile.objects.create(user=self.regular_user, user_type='regular')

    def test_login_page_loads(self):
        """测试登录页面加载"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/login.html')

    def test_admin_login_redirect(self):
        """测试管理员登录跳转""
        response = self.client.post(reverse('login'), {
            'username': 'admin',
            'password': 'admin123'
        })
        self.assertRedirects(response, reverse('admin_dashboard'))

    def test_regular_login_redirect(self):
        """测试普通用户登录跳转""
        response = self.client.post(reverse('login'), {
            'username': 'user1',
            'password': 'user123'
        })
        self.assertRedirects(response, reverse('court_list'))

    def test_login_wrong_password(self):
        """测试错误密码登录"""
        response = self.client.post(reverse('login'), {
            'username': 'admin',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '用户名或密码错误')

    def test_logout(self):
        """测试登出"""
        self.client.login(username='user1', password='user123')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))


class CourtListTests(TestCase):
    """场地预约页面测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='user1',
            password='user123'
        )
        Profile.objects.create(user=self.user, user_type='regular')

        self.court_type, _ = CourtType.objects.get_or_create(
            name='羽毛球场',
            defaults={'is_default': False}
        )
        self.court = Court.objects.create(
            court_type=self.court_type,
            name='羽毛球场A',
            court_number='1'
        )
        CourtAvailability.objects.create(
            court=self.court,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            start_time=time(9, 0),
            end_time=time(21, 0)
        )
        self.client.login(username='user1', password='user123')

    def test_court_list_page_loads(self):
        """测试场地列表页面加载"""
        response = self.client.get(reverse('court_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/court_list.html')

    def test_court_list_shows_courts(self):
        """测试场地列表显示场地"""
        response = self.client.get(reverse('court_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '场地预约')

    def test_get_time_slots_api(self):
        """测试获取时间段API"""
        response = self.client.get(
            reverse('get_time_slots'),
            {'date': date.today().isoformat()}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('courts', data)
        self.assertIn('server_time', data)

    def test_create_booking_api(self):
        """测试创建预约API"""
        response = self.client.post(
            reverse('create_booking_api'),
            {
                'court_id': self.court.id,
                'date': date.today().isoformat(),
                'start_time': '10:00',
                'end_time': '10:30',
                'booker_name': '测试用户',
                'booker_phone': '13800138000'
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success', False))

    def test_my_bookings_page(self):
        """测试我的预约页面"""
        response = self.client.get(reverse('my_bookings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/my_bookings.html')

    def test_cancel_booking(self):
        """测试取消预约"""
        booking = Booking.objects.create(
            user=self.user,
            court=self.court,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(10, 30),
            booker_name='测试用户',
            booker_phone='13800138000'
        )
        response = self.client.get(reverse('cancel_booking', args=[booking.id]))
        self.assertRedirects(response, reverse('my_bookings'))
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')


class AdminTests(TestCase):
    """管理后台测试"""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123'
        )
        Profile.objects.create(user=self.admin_user, user_type='admin')

        self.court_type, _ = CourtType.objects.get_or_create(
            name='羽毛球场',
            defaults={'is_default': False}
        )
        self.court = Court.objects.create(
            court_type=self.court_type,
            name='羽毛球场A',
            court_number='1'
        )
        self.client.login(username='admin', password='admin123')

    def test_admin_dashboard(self):
        """测试管理仪表盘""
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/admin/admin_dashboard.html')

    def test_admin_court_list(self):
        """测试场地管理页面"""
        response = self.client.get(reverse('admin_court_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/admin/admin_court_list.html')

    def test_admin_add_court(self):
        """测试添加场地"""
        response = self.client.post(reverse('admin_court_add'), {
            'court_type': self.court_type.id,
            'name': '羽毛球场B',
            'court_number': '2',
            'description': ''
        })
        self.assertRedirects(response, reverse('admin_court_list'))
        self.assertTrue(Court.objects.filter(name='羽毛球场B').exists())

    def test_admin_edit_court(self):
        """测试编辑场地"""
        response = self.client.post(reverse('admin_court_edit', args=[self.court.id]), {
            'court_type': self.court_type.id,
            'name': '羽毛球场A-修改',
            'court_number': '1',
            'description': ''
        })
        self.assertRedirects(response, reverse('admin_court_list'))
        self.court.refresh_from_db()
        self.assertEqual(self.court.name, '羽毛球场A-修改')

    def test_admin_delete_court(self):
        """测试删除场地"""
        response = self.client.get(reverse('admin_court_delete', args=[self.court.id]))
        self.assertRedirects(response, reverse('admin_court_list'))
        self.assertFalse(Court.objects.filter(id=self.court.id).exists())

    def test_admin_availability_list(self):
        """测试可用时间段管理""
        response = self.client.get(reverse('admin_availability_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/admin/admin_availability_list.html')

    def test_admin_add_availability(self):
        """测试添加可用时间段""
        response = self.client.post(reverse('admin_availability_add'), {
            'court': self.court.id,
            'start_date': date.today().isoformat(),
            'end_date': (date.today() + timedelta(days=7)).isoformat(),
            'start_time': '09:00',
            'end_time': '21:00'
        })
        self.assertRedirects(response, reverse('admin_availability_list'))
        self.assertTrue(CourtAvailability.objects.filter(court=self.court).count() >= 1)

    def test_admin_bookings(self):
        """测试预约管理页面"""
        response = self.client.get(reverse('admin_bookings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/admin/admin_bookings.html')

    def test_admin_student_list(self):
        """测试学员管理页面"""
        response = self.client.get(reverse('admin_student_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/admin/admin_student_list.html')

    def test_admin_add_student(self):
        """测试添加学员"""
        response = self.client.post(reverse('admin_student_add'), {
            'name': '张三',
            'phone': '13900139000',
            'total_class_hours': 20
        })
        self.assertRedirects(response, reverse('admin_student_list'))
        self.assertTrue(Student.objects.filter(name='张三').exists())

    def test_admin_edit_student(self):
        """测试编辑学员"""
        student = Student.objects.create(name='李四', phone='13900139001', total_class_hours=10)
        response = self.client.post(reverse('admin_student_edit', args=[student.id]), {
            'name': '李四-修改',
            'phone': '13900139001',
            'total_class_hours': 15
        })
        self.assertRedirects(response, reverse('admin_student_list'))
        student.refresh_from_db()
        self.assertEqual(student.name, '李四-修改')
        self.assertEqual(student.total_class_hours, 15)

    def test_admin_delete_student(self):
        """测试删除学员"""
        student = Student.objects.create(name='王五', phone='13900139002', total_class_hours=5)
        response = self.client.get(reverse('admin_student_delete', args=[student.id]))
        self.assertRedirects(response, reverse('admin_student_list'))
        self.assertFalse(Student.objects.filter(id=student.id).exists())

    def test_admin_course_booking_list(self):
        """测试课程预约列表"""
        response = self.client.get(reverse('admin_course_booking_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/admin/admin_course_booking_list.html')


class PermissionTests(TestCase):
    """权限测试"""

    def setUp(self):
        self.client = Client()
        self.regular_user = User.objects.create_user(
            username='user1',
            password='user123'
        )
        Profile.objects.create(user=self.regular_user, user_type='regular')

    def test_regular_user_cannot_access_admin(self):
        """测试普通用户无法访问管理后台""
        self.client.login(username='user1', password='user123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_user_redirected_to_login(self):
        """测试未登录用户跳转到登录页""
        response = self.client.get(reverse('court_list'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))
