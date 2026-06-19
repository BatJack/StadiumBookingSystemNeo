---
name: "stadium-booking-context"
description: "Provides project structure, URL routing rules, and UI editing guidelines for Stadium Booking System. Invoke BEFORE modifying any code to understand project architecture and avoid URL conflicts."
---

# 体育场馆预约系统 - 项目约束文件

## 项目概述
Django 场馆预约系统，支持场地预约和教培课程管理。

## 用户类型与权限

| 用户类型 | 标识 | 权限范围 |
|---------|------|---------|
| 超级管理员 | `super_admin` | 全部管理功能 + 用户管理 |
| 管理员 | `admin` | 全部管理功能 |
| 普通用户 | `regular` | 场地预约、查看自己的预约 |

### 权限检查函数
```python
# views.py
def is_admin_user(user):
    return user.profile.user_type in ('admin', 'super_admin')

def is_super_admin_user(user):
    return user.profile.user_type == 'super_admin'
```

## 页面结构与导航

### 导航栏逻辑（base.html）
```
所有登录用户:
├── 场地列表 (court_list) - 所有用户可见
├── 我的预约 (my_bookings) - 仅 regular 用户
├── 教培管理 (training_dashboard) - 仅 admin/super_admin
├── 管理后台 (admin_dashboard) - 仅 admin/super_admin
└── 退出登录 (logout)
```

### 页面层级

#### 用户页面
| 页面 | URL | 模板路径 | 访问权限 |
|-----|-----|---------|---------|
| 登录 | `/` | `booking/login.html` | 未登录用户 |
| 场地列表 | `/courts/` | `booking/court_list.html` | 所有登录用户 |
| 我的预约 | `/my-bookings/` | `booking/my_bookings.html` | regular 用户 |
| 预约表单 | `/api/create-booking/` | `booking/booking_form.html` | 所有登录用户 |

#### 管理后台页面（admin/super_admin）
| 页面 | URL | 模板路径 | 说明 |
|-----|-----|---------|------|
| 管理后台首页 | `/manage/` | `admin/admin_dashboard.html` | 卡片式导航 |
| 数据统计 | `/manage/statistics/` | `admin/admin_statistics.html` | |
| 场地管理 | `/manage/courts/` | `admin/admin_court_list.html` | |
| 可用时段 | `/manage/availabilities/` | `admin/admin_availability_list.html` | |
| 预约管理 | `/manage/bookings/` | `admin/admin_bookings.html` | |
| 用户管理 | `/manage/users/` | `admin/admin_user_list.html` | 仅 super_admin |

#### 教培管理页面（admin/super_admin）
| 页面 | URL | 模板路径 | 说明 |
|-----|-----|---------|------|
| 教培管理首页 | `/manage/training/` | `admin/training_dashboard.html` | 卡片式导航 |
| 学员管理 | `/manage/students/` | `admin/admin_student_list.html` | |
| 课程预约 | `/manage/course-bookings/` | `admin/admin_course_booking_list.html` | |

## 数据模型关系

```
User (1) ── (1) Profile (user_type: super_admin/admin/regular)
  │
  └── (1:N) Booking (booking_type: court/course)
              │
              └── (1:N) BookingStudent ── Student (N:1)
                                           │
                                           └── total_class_hours

Court (N:1) CourtType
  │
  ├── (1:N) CourtAvailability (start_date, end_date, start_time, end_time)
  │
  └── (1:N) Booking
```

## UI 风格规范

### 管理后台/教培管理卡片样式
- 容器: `.dashboard-container` (max-width: 1000px)
- 卡片: `.dashboard-card` (白色背景, 3px #ecf0f1 边框, 顶部 4px 色条)
- 管理卡片: `.management-card` (#ecf0f1 背景, 3px #bdc3c7 边框)
- 管理后台主色: `#3498db` (蓝色)
- 教培管理主色: `#9b59b6` (紫色)

### 颜色变量（base.html）
```css
--primary: #4F46E5;
--success: #10B981;
--danger: #EF4444;
--warning: #F59E0B;
--radius-sm: 4px;
--radius: 8px;
--radius-lg: 12px;
```

## 修改注意事项

### 添加新页面时
1. 在 `urls.py` 添加路由，避免路径冲突
2. 在 `views.py` 添加视图函数，添加权限检查
3. 在 `templates/booking/` 或 `templates/booking/admin/` 创建模板
4. 如需导航入口，修改 `base.html` 的 `.nav` 区域

### 修改导航栏时
1. 注意用户类型条件判断
2. 保持与现有样式一致
3. 使用 `{% url 'name' %}` 模板标签

### 修改管理页面时
1. 区分管理后台（蓝色主题）和教培管理（紫色主题）
2. 卡片样式使用 `.management-card` 类
3. 响应式断点: 768px, 480px

## 常用模板标签

```django
{% extends 'booking/base.html' %}
{% block title %}页面标题{% endblock %}
{% block content %}页面内容{% endblock %}

{% url 'court_list' %}
{% url 'admin_dashboard' %}
{% url 'training_dashboard' %}

{% if user.profile.user_type == 'admin' or user.profile.user_type == 'super_admin' %}
{% if is_super_admin %}
```
