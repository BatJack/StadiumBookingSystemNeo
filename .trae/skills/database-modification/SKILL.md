---
name: "database-modification"
description: "Guides database modification for the stadium booking system. Invoke when user asks to modify/add/delete models, fields, or run migrations."
---

# 数据库修改指南

## 核心数据表

| 表名 | 模型类 | 说明 |
|------|--------|------|
| auth_user | User | Django内置用户表 |
| booking_profile | Profile | 用户类型扩展（super_admin/admin/regular） |
| booking_courttype | CourtType | 场地类型（篮球场、网球场等） |
| booking_court | Court | 场地表（含场馆、编号，名称自动生成） |
| booking_courtavailability | CourtAvailability | 场地可用时间段 |
| booking_booking | Booking | 统一预约模型（场地/课程） |
| booking_student | Student | 学员信息（含课时） |
| booking_bookingstudent | BookingStudent | 预约-学员关联表 |
| booking_coach | Coach | 教练信息（含课时统计） |
| booking_coachstudent | CoachStudent | 教练-学员授课关联表 |

## Court 模型字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| court_type | ForeignKey | 场地类型（篮球场、羽毛球场等） |
| building | CharField | 所属场馆（A馆-Z馆，26个选项） |
| court_number | IntegerField | 场地编号（1-99号） |
| name | CharField | 场地名称（自动生成，格式：场地类型 + 所属场馆 + 场地编号） |
| description | TextField | 场地描述 |

**命名规则**：场地名称由系统自动生成，例如"篮球场 A馆 1号"，用户无需手动输入。

## 业务逻辑要点

1. **课时系统**：30分钟=1课时，添加/移除学员时扣/退课时
2. **时间规则**：预约时间必须是整点或半点
3. **状态管理**：`active`=有效，`cancelled`=已取消
4. **场地类型**：默认5种（篮球场、网球场、羽毛球场、匹克球场、台球场），管理员可自定义

## 修改流程

```bash
# 1. 修改 models.py
# 2. 创建迁移
conda run -n django python manage.py makemigrations booking

# 3. 执行迁移
conda run -n django python manage.py migrate

# 4. 验证
conda run -n django python manage.py shell
```

## 注意事项

- 修改外键注意CASCADE策略
- 课时变动需事务一致性
- 涉及时间字段需整点或半点验证

## 相关文件

- 模型：`booking/models.py`
- 视图：`booking/views.py`
- 迁移：`booking/migrations/`
- 文档：`.trae/docs/database-schema.md`
