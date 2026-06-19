from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    USER_TYPE_CHOICES = [
        ('super_admin', '超级管理员'),
        ('admin', '管理员'),
        ('regular', '普通用户'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='用户')
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='regular', verbose_name='用户类型')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '用户类型'
        verbose_name_plural = '用户类型'

    def __str__(self):
        return f'{self.user.username} - {self.get_user_type_display()}'


class Student(models.Model):
    name = models.CharField(max_length=100, verbose_name='学员姓名')
    phone = models.CharField(max_length=20, verbose_name='联系电话')
    total_class_hours = models.IntegerField(default=0, verbose_name='课时总数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '学员'
        verbose_name_plural = '学员'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} - {self.phone}'


class CourtType(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='场地类型名称')
    is_default = models.BooleanField(default=False, verbose_name='系统默认类型')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '场地类型'
        verbose_name_plural = '场地类型'
        ordering = ['name']

    def __str__(self):
        return self.name


class Court(models.Model):
    court_type = models.ForeignKey(CourtType, on_delete=models.PROTECT, related_name='courts', verbose_name='场地类型', null=True, blank=True)
    name = models.CharField(max_length=100, verbose_name='场地名称')
    court_number = models.CharField(max_length=20, blank=True, verbose_name='场地编号')
    description = models.TextField(blank=True, verbose_name='场地描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '场地'
        verbose_name_plural = '场地'
        ordering = ['court_type__name', 'court_number', 'id']

    def __str__(self):
        if self.court_type and self.court_number:
            return f'{self.court_type.name} - {self.court_number}'
        return self.name


class CourtAvailability(models.Model):
    court = models.ForeignKey(Court, on_delete=models.CASCADE, related_name='availabilities', verbose_name='场地')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(verbose_name='结束日期')
    start_time = models.TimeField(verbose_name='每天开始时间')
    end_time = models.TimeField(verbose_name='每天结束时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '场地可用时间段'
        verbose_name_plural = '场地可用时间段'
        ordering = ['start_date', 'start_time']

    def __str__(self):
        return f'{self.court.name} - {self.start_date} 至 {self.end_date} {self.start_time}-{self.end_time}'

    def is_date_available(self, date):
        return self.start_date <= date <= self.end_date


class Booking(models.Model):
    BOOKING_TYPE_CHOICES = [
        ('court', '场地预约'),
        ('course', '课程预约'),
    ]

    STATUS_CHOICES = [
        ('active', '有效'),
        ('cancelled', '已取消'),
    ]

    booking_type = models.CharField(max_length=20, choices=BOOKING_TYPE_CHOICES, default='court', verbose_name='预约类型')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', verbose_name='用户', null=True, blank=True)
    court = models.ForeignKey(Court, on_delete=models.CASCADE, related_name='bookings', verbose_name='场地')
    date = models.DateField(verbose_name='预约日期')
    start_time = models.TimeField(verbose_name='开始时间')
    end_time = models.TimeField(verbose_name='结束时间')
    booker_name = models.CharField(max_length=100, verbose_name='预约人姓名', null=True, blank=True)
    booker_phone = models.CharField(max_length=20, verbose_name='预约人联系方式', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '预约'
        verbose_name_plural = '预约'
        ordering = ['date', 'start_time']

    def __str__(self):
        if self.booking_type == 'course':
            return f'课程 - {self.court.name} - {self.date} {self.start_time}-{self.end_time}'
        return f'{self.booker_name} - {self.court.name} - {self.date} {self.start_time}-{self.end_time}'

    def is_court_booking(self):
        return self.booking_type == 'court'

    def is_course_booking(self):
        return self.booking_type == 'course'

    def get_student_count(self):
        return self.students.count()

    def get_total_class_hours(self):
        return sum(cs.class_hours for cs in self.students.all())


class BookingStudent(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='students', verbose_name='预约')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='bookings', verbose_name='学员')
    class_hours = models.IntegerField(verbose_name='扣除课时数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '预约学员'
        verbose_name_plural = '预约学员'
        unique_together = ['booking', 'student']

    def __str__(self):
        return f'{self.booking} - {self.student.name} ({self.class_hours}课时)'
