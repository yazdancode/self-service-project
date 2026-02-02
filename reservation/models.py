from django.db import models

from accounts.models import User
from menu.models import DailyMenu


class FoodReservation(models.Model):
    RESERVATION_STATUS = (
        ("pending", "در انتظار"),
        ("confirmed", "تأیید شده"),
        ("cancelled", "لغو شده"),
        ("delivered", "تحویل داده شده"),
        ("absent", "غایب"),
    )

    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="دانشجو")
    menu = models.ForeignKey(DailyMenu, on_delete=models.CASCADE, verbose_name="منو")
    reservation_date = models.DateTimeField(
        auto_now_add=True, verbose_name="تاریخ رزرو"
    )
    meal_date = models.DateField(verbose_name="تاریخ غذا")
    status = models.CharField(
        max_length=20,
        choices=RESERVATION_STATUS,
        default="pending",
        verbose_name="وضعیت",
    )
    qr_code = models.ImageField(
        upload_to="reservation_qrcodes/", blank=True, null=True, verbose_name="کد qr"
    )
    special_request = models.TextField(
        blank=True, null=True, verbose_name="درخواست ویژه"
    )

    def __str__(self):
        return f"{self.student.username} - {self.menu.get_meal_type_display()} - {self.meal_date}"

    class Meta:
        verbose_name = "رزرو غذا"
        verbose_name_plural = "رزرو غذا"


class ReservationSettings(models.Model):
    reservation_deadline = models.TimeField(verbose_name="مهلت رزرو")
    cancellation_deadline = models.TimeField(verbose_name="مهلت لغو")
    max_daily_reservations = models.IntegerField(
        default=3, verbose_name="حداکثر رزرو روزانه"
    )
    can_reserve_for_next_days = models.IntegerField(
        default=7, verbose_name="می توانید برای روزهای آینده رزرو کنید"
    )

    def __str__(self):
        return self.reservation_deadline

    class Meta:
        verbose_name = "تنظیمات رزرو"
        verbose_name_plural = "تنظیمات رزرو"
