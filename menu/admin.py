from django.contrib import admin
from .models import (
    FoodCategory, FoodItem, DailyMenu, MenuFoodItem,
    Transaction, FreeRestaurantMenu, FreeRestaurantReservation
)


@admin.register(FoodCategory)
class FoodCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'calories', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('name',)


class MenuFoodItemInline(admin.TabularInline):
    model = MenuFoodItem
    extra = 1


@admin.register(DailyMenu)
class DailyMenuAdmin(admin.ModelAdmin):
    list_display = ('date', 'meal_type', 'price', 'capacity', 'reserved_count', 'is_active')
    list_filter = ('date', 'meal_type', 'is_active')
    search_fields = ('date',)
    list_editable = ('is_active',)
    inlines = [MenuFoodItemInline]
    date_hierarchy = 'date'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'balance_after', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('user__username', 'description')
    ordering = ('-created_at',)


@admin.register(FreeRestaurantMenu)
class FreeRestaurantMenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'meal_type', 'price', 'is_available')
    list_filter = ('meal_type', 'is_available')
    search_fields = ('name',)


@admin.register(FreeRestaurantReservation)
class FreeRestaurantReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'menu_item', 'reservation_date', 'status')
    list_filter = ('status', 'reservation_date')
    search_fields = ('user__username', 'menu_item__name')
    ordering = ('-reservation_date',)