from django.db import models


class AppUser(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=64, unique=True)
    password_hash = models.CharField(max_length=255)
    display_name = models.CharField(max_length=64)
    needs_password_reset = models.BooleanField(db_column='needs_password_reset', default=False)

    class Meta:
        db_table = 'app_users'
        managed = False


class PermissionGroup(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=255, blank=True)
    can_manage_projects = models.BooleanField(default=False)
    can_manage_tasks = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)
    can_manage_permissions = models.BooleanField(default=False)
    can_view_all_tasks = models.BooleanField(default=False)
    can_edit_all_tasks = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        db_table = 'permission_groups'
        ordering = ['name']


class UserProfile(models.Model):
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE, primary_key=True, db_column='user_id')
    department = models.ForeignKey('projects.Department', on_delete=models.SET_NULL, null=True, blank=True)
    permission_group = models.ForeignKey(PermissionGroup, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.display_name or self.user.username} Profile"

    class Meta:
        db_table = 'user_profiles'
        ordering = ['user__username']
