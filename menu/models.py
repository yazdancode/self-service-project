from django.db import models

from accounts.models import User


class FoodCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام دسته‌بندی")
    description = models.TextField(blank=True, verbose_name="توضیحات")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "دسته‌بندی غذا"
        verbose_name_plural = "دسته‌بندی‌های غذا"


class FoodItem(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام غذا")
    category = models.ForeignKey(
        FoodCategory, on_delete=models.CASCADE, verbose_name="دسته‌بندی"
    )
    description = models.TextField(blank=True, verbose_name="توضیحات")
    calories = models.IntegerField(blank=True, null=True, verbose_name="کالری")
    image = models.ImageField(upload_to="images/", verbose_name="تصویر")
    is_available = models.BooleanField(default=True, verbose_name="وضعیت فعال بودن")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "غذا"
        verbose_name_plural = "غذاها"
        ordering = ["name"]


class DailyMenu(models.Model):
    date = models.DateField(verbose_name="تاریخ")
    meal_type = models.CharField(
        max_length=20,
        verbose_name="وعده غذایی",
        choices=[
            ("breakfast", "صبحانه"),
            ("lunch", "ناهار"),
            ("dinner", "شام"),
        ],
    )
    food_items = models.ManyToManyField(
        FoodItem, through="MenuFoodItem", verbose_name="مواد غذایی"
    )
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="قیمت")
    capacity = models.IntegerField(verbose_name="ظرفیت")
    reserved_count = models.IntegerField(default=0, verbose_name="تعداد رزرو شده")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")

    def __str__(self):
        return f"{self.get_meal_type_display()} - {self.date}"

    def available_capacity(self):
        return self.capacity - self.reserved_count

    available_capacity.short_description = "ظرفیت باقی‌مانده"

    class Meta:
        verbose_name = "منوی روزانه"
        verbose_name_plural = "منوهای روزانه"
        ordering = ["-date", "meal_type"]


class MenuFoodItem(models.Model):
    menu = models.ForeignKey(DailyMenu, on_delete=models.CASCADE, verbose_name="منو")
    food_item = models.ForeignKey(
        FoodItem, on_delete=models.CASCADE, verbose_name="غذا"
    )
    quantity = models.CharField(max_length=50, verbose_name="مقدار")

    def __str__(self):
        return f"{self.food_item.name} - {self.quantity}"

    class Meta:
        verbose_name = "آیتم منو"
        verbose_name_plural = "آیتم‌های منو"
        unique_together = ["menu", "food_item"]


class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = (
        ("charge", "شارژ"),
        ("reserve", "رزرو غذا"),
        ("cancel", "لغو رزرو"),
        ("refund", "بازگشت وجه"),
        ("transfer", "انتقال"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    transaction_type = models.CharField(
        max_length=20, choices=TRANSACTION_TYPE_CHOICES, verbose_name="نوع تراکنش"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="مبلغ")
    balance_after = models.DecimalField(
        max_digits=10, decimal_places=0, verbose_name="مانده حساب"
    )
    description = models.TextField(blank=True, verbose_name="شرح")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ انجام")

    def __str__(self):
        return f"{self.user.username} - {self.get_transaction_type_display()} - {self.amount}"

    class Meta:
        verbose_name = "تراکنش"
        verbose_name_plural = "تراکنش‌ها"
        ordering = ["-created_at"]



class FreeRestaurantMenu(models.Model):
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'صبحانه'),
        ('lunch', 'ناهار'),
        ('dinner', 'شام'),
    ]

    name = models.CharField(max_length=200, verbose_name="نام غذا")
    meal_type = models.CharField(
        max_length=20,
        choices=MEAL_TYPE_CHOICES,
        verbose_name="وعده غذایی"
    )
    description = models.TextField(blank=True, verbose_name="توضیحات")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="قیمت")
    is_available = models.BooleanField(default=True, verbose_name="در دسترس")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    def __str__(self):
        return f"{self.get_meal_type_display()} - {self.name}"

    class Meta:
        verbose_name = "منوی رستوران آزاد"
        verbose_name_plural = "منوهای رستوران آزاد"
        ordering = ['meal_type', 'name']


class FreeRestaurantReservation(models.Model):
    RESERVATION_STATUS_CHOICES = [
        ('reserved', 'رزرو شده'),
        ('cancelled', 'لغو شده'),
        ('consumed', 'مصرف شده'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    menu_item = models.ForeignKey(FreeRestaurantMenu, on_delete=models.CASCADE, verbose_name="غذا")
    reservation_date = models.DateField(verbose_name="تاریخ رزرو")
    status = models.CharField(
        max_length=20,
        choices=RESERVATION_STATUS_CHOICES,
        default='reserved',
        verbose_name="وضعیت"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    def __str__(self):
        return f"{self.user.username} - {self.menu_item.name} - {self.reservation_date}"

    class Meta:
        verbose_name = "رزرو رستوران آزاد"
        verbose_name_plural = "رزروهای رستوران آزاد"
        unique_together = ['user', 'menu_item', 'reservation_date']