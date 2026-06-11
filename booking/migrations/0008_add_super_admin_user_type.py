from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0007_add_default_court_types'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='user_type',
            field=models.CharField(choices=[('super_admin', '超级管理员'), ('admin', '管理员'), ('regular', '普通用户')], default='regular', max_length=20, verbose_name='用户类型'),
        ),
    ]
