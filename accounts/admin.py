from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    list_display = (
        "username",
        "student_id",
        "role",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "role",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "username",
        "student_id",
        "email",
    )

    ordering = ("username",)

    fieldsets = UserAdmin.fieldsets + (
        (
            "اطلاعات کاربر",
            {
                "fields": (
                    "role",
                    "student_id",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "اطلاعات کاربر",
            {
                "fields": (
                    "role",
                    "student_id",
                )
            },
        ),
    )
