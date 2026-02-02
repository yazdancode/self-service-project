from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class CustomUserManager(DjangoUserManager):
    def create_user(self, student_id, password=None, **extra_fields):
        if "username" not in extra_fields or not extra_fields["username"]:
            extra_fields["username"] = student_id
        return super().create_user(
            student_id=student_id, password=password, **extra_fields
        )

    def create_superuser(self, student_id, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if "username" not in extra_fields or not extra_fields["username"]:
            extra_fields["username"] = student_id
        return super().create_superuser(
            student_id=student_id, password=password, **extra_fields
        )


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "دانشجو"
        OSTAD = "ostad", "استاد"

    student_id = models.CharField(
        max_length=10, unique=True, null=True, blank=True, verbose_name="شناسه دانشجویی"
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        verbose_name="نقش کاربر",
    )

    USERNAME_FIELD = "student_id"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.student_id


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="کاربر")
    balance = models.DecimalField(
        max_digits=10, decimal_places=0, default=0, verbose_name="موجودی"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")

    def __str__(self):
        return f"{self.user.username} - {self.balance} تومان"

    class Meta:
        verbose_name = "کیف پول"
        verbose_name_plural = "کیف پول‌ها"


@receiver(post_save, sender=User)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)
