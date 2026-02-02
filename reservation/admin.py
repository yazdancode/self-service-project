from django.contrib import admin
from django.utils.html import format_html

from .models import FoodReservation, ReservationSettings


@admin.register(FoodReservation)
class FoodReservationAdmin(admin.ModelAdmin):
    list_display = (
        "student_username",
        "menu_display",
        "meal_date",
        "status_badge",
        "reservation_date_formatted",
        "special_request_preview",
    )
    list_filter = (
        "status",
        "meal_date",
        "reservation_date",
        "menu__meal_type",
        "menu__date",
    )
    search_fields = (
        "student__username",
        "student__first_name",
        "student__last_name",
        "menu__id",
    )
    readonly_fields = ("reservation_date", "qr_code_preview")
    date_hierarchy = "meal_date"
    ordering = ("-reservation_date",)

    fieldsets = (
        ("اطلاعات پایه", {"fields": ("student", "menu", "meal_date", "status")}),
        ("جزئیات رزرو", {"fields": ("reservation_date", "special_request")}),
        ("کد QR", {"fields": ("qr_code_preview", "qr_code"), "classes": ("collapse",)}),
    )

    def student_username(self, obj):
        return f"{obj.student.get_full_name() or obj.student.username}"

    student_username.short_description = "دانشجو"
    student_username.admin_order_field = "student__username"

    def menu_display(self, obj):
        return f"{obj.menu.get_meal_type_display()} - {obj.menu.date}"

    menu_display.short_description = "منو"
    menu_display.admin_order_field = "menu__date"

    def status_badge(self, obj):
        colors = {
            "pending": "#ff9800",
            "confirmed": "#4caf50",
            "cancelled": "#f44336",
            "delivered": "#2196f3",
            "absent": "#9e9e9e",
        }
        color = colors.get(obj.status, "#9e9e9e")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; '
            'border-radius: 12px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "وضعیت"

    def reservation_date_formatted(self, obj):
        return obj.reservation_date.strftime("%Y/%m/%d %H:%M")

    reservation_date_formatted.short_description = "تاریخ رزرو"
    reservation_date_formatted.admin_order_field = "reservation_date"

    def special_request_preview(self, obj):
        if obj.special_request:
            preview = (
                obj.special_request[:50] + "..."
                if len(obj.special_request) > 50
                else obj.special_request
            )
            return preview
        return "-"

    special_request_preview.short_description = "درخواست ویژه"

    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px; border: 1px solid #ddd; border-radius: 4px;" />',
                obj.qr_code.url,
            )
        return "بدون کد QR"

    qr_code_preview.short_description = "پیش‌نمایش کد QR"


@admin.register(ReservationSettings)
class ReservationSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "reservation_deadline_formatted",
        "cancellation_deadline_formatted",
        "max_daily_reservations",
        "can_reserve_for_next_days",
    )

    def reservation_deadline_formatted(self, obj):
        return obj.reservation_deadline.strftime("%H:%M")

    reservation_deadline_formatted.short_description = "مهلت رزرو"

    def cancellation_deadline_formatted(self, obj):
        return obj.cancellation_deadline.strftime("%H:%M")

    cancellation_deadline_formatted.short_description = "مهلت لغو"

    def has_add_permission(self, request):
        # فقط یک رکورد تنظیمات مجاز باشد
        return not ReservationSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # حذف تنظیمات مجاز نباشد
        return False
