# Generated manually to add HR role to Employee model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0026_alter_leadforward_unique_together_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='role',
            field=models.CharField(
                choices=[
                    ('employee', 'Employee'),
                    ('team_leader', 'Team Leader'),
                    ('manager', 'Manager'),
                    ('hr', 'HR'),
                    ('admin', 'Admin'),
                    ('superadmin', 'SuperAdmin'),
                ],
                default='employee',
                max_length=20
            ),
        ),
    ]
