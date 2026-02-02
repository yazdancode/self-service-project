from datetime import date, timedelta
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.models import User, Wallet
from menu.models import DailyMenu, Transaction, FreeRestaurantMenu, FreeRestaurantReservation
from reservation.models import FoodReservation
from jdatetime import date as jdate

class MenuView(LoginRequiredMixin, View):

    template_name = "menu/index.html"

    def get(self, request):
        try:
            user = get_object_or_404(User, id=request.user.id)

            context = {
                "user": user,
                "is_authenticated": request.user.is_authenticated,
            }
            return render(request, self.template_name, context)
        except Exception as e:
            print(f"Error in MenuView: {e}")
            context = {"error": "خطا در بارگذاری منو"}
            return render(request, "menu/error.html", context, status=500)


class SaleDayView(LoginRequiredMixin, View):
    template_name = "menu/sale_day.html"

    def get(self, request):
        week_offset = int(request.GET.get("week_offset", 0))
        today = date.today()
        start_of_week = (
            today - timedelta(days=today.weekday()) + timedelta(days=week_offset)
        )
        end_of_week = start_of_week + timedelta(days=6)

        # دریافت همه منوهای فعال (شامل صبحانه)
        menus = DailyMenu.objects.filter(
            date__range=[start_of_week, end_of_week], is_active=True
        ).order_by("date", "meal_type")

        menus_by_date = []
        current = start_of_week
        while current <= end_of_week:
            day_menus = [m for m in menus if m.date == current]
            if day_menus:
                menus_by_date.append({"date": current, "menus": day_menus})
            current += timedelta(days=1)

        # دریافت رزروهای کاربر (همه وعده‌ها)
        user_reservations = FoodReservation.objects.filter(
            student=request.user, meal_date__range=[start_of_week, end_of_week]
        ).values_list("menu_id", flat=True)

        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        wallet_balance = intcomma(wallet.balance) if wallet.balance else "0"

        context = {
            "today": today,
            "menus_by_date": menus_by_date,
            "user_reservations": set(user_reservations),
            "week_offset": week_offset,
            "wallet_balance": wallet_balance,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        menu_id = request.POST.get("menu_id")

        if not menu_id:
            messages.error(request, "منوی معتبر انتخاب نشده است.")
            return redirect("menu:sale_day")

        menu = get_object_or_404(DailyMenu, id=menu_id, is_active=True)

        # ✅ بررسی رزرو تکراری برای همه وعده‌ها
        if FoodReservation.objects.filter(student=request.user, menu=menu).exists():
            messages.warning(
                request, f"شما قبلاً «{menu.get_meal_type_display()}» را رزرو کرده‌اید."
            )
            return redirect("menu:sale_day")

        # ✅ بررسی ظرفیت برای همه وعده‌ها
        if menu.reserved_count >= menu.capacity:
            messages.error(
                request, f"ظرفیت {menu.get_meal_type_display()} تکمیل شده است."
            )
            return redirect("menu:sale_day")

        # ✅ بررسی موجودی کیف پول
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        if wallet.balance < menu.price:
            required_amount = intcomma(menu.price)
            messages.error(
                request, f"موجودی کافی ندارید. مبلغ {required_amount} تومان نیاز است."
            )
            return redirect("menu:sale_day")

        try:
            with transaction.atomic():
                # ✅ ایجاد رزرو برای همه وعده‌ها
                FoodReservation.objects.create(
                    student=request.user,
                    menu=menu,
                    meal_date=menu.date,
                    status="pending",
                )

                # کسر مبلغ
                wallet.balance -= menu.price
                wallet.save()

                # افزایش ظرفیت
                menu.reserved_count += 1
                menu.save()

            success_amount = intcomma(menu.price)
            messages.success(
                request,
                f"{menu.get_meal_type_display()} به مبلغ {success_amount} تومان با موفقیت رزرو شد! ✅",
            )
        except Exception as e:
            messages.error(request, "خطا در ثبت رزرو. لطفاً دوباره تلاش کنید.")

        return redirect("menu:sale_day")


class CancelReservationView(LoginRequiredMixin, View):
    """لغو رزرو برای همه وعده‌ها"""

    def post(self, request, reservation_id):
        reservation = get_object_or_404(
            FoodReservation, id=reservation_id, student=request.user
        )

        if reservation.status not in ["pending", "confirmed"]:
            messages.error(request, "این رزرو قابل لغو نیست.")
            return redirect("menu:sale_day")

        if reservation.meal_date < date.today():
            messages.error(request, "نمی‌توانید رزرو روزهای گذشته را لغو کنید.")
            return redirect("menu:sale_day")

        menu = reservation.menu

        try:
            with transaction.atomic():
                # بازگشت مبلغ
                wallet, _ = Wallet.objects.select_for_update().get_or_create(
                    user=request.user
                )
                wallet.balance += menu.price
                wallet.save()

                # حذف رزرو
                reservation.delete()

                # کاهش ظرفیت
                if menu.reserved_count > 0:
                    menu.reserved_count -= 1
                    menu.save()

            refund_formatted = intcomma(menu.price)
            messages.success(
                request,
                f"رزرو {menu.get_meal_type_display()} لغو شد و {refund_formatted} تومان به کیف پول شما بازگشت! 💰",
            )
        except Exception as e:
            messages.error(request, "خطا در لغو رزرو.")

        return redirect("menu:sale_day")







class FreeRestaurantView(LoginRequiredMixin, View):
    template_name = "menu/free_restaurant.html"

    def get(self, request):
        # دریافت روز هفته فارسی
        today = date.today()
        j_today = jdate.fromgregorian(date=today)
        persian_weekday = j_today.strftime('%A')

        # تبدیل نام روزهای هفته به انگلیسی برای فیلتر
        weekday_mapping = {
            'شنبه': 6,  # Saturday
            'یک‌شنبه': 0,  # Sunday
            'دوشنبه': 1,  # Monday
            'سه‌شنبه': 2,  # Tuesday
            'چهارشنبه': 3,  # Wednesday
            'پنج‌شنبه': 4,  # Thursday
            'جمعه': 5,  # Friday
        }

        # محاسبه تاریخ جاری بر اساس روز هفته
        current_weekday = today.weekday()  # Monday=0, Sunday=6
        selected_day = request.GET.get('day', persian_weekday)
        target_weekday = weekday_mapping.get(selected_day, current_weekday)

        # محاسبه تاریخ هدف
        if target_weekday == current_weekday:
            target_date = today
        else:
            days_ahead = target_weekday - current_weekday
            if days_ahead <= 0:
                days_ahead += 7
            target_date = today + timedelta(days=days_ahead)

        # دریافت منوهای فعال
        menus = FreeRestaurantMenu.objects.filter(is_available=True).order_by('meal_type')

        # گروه‌بندی بر اساس وعده
        menus_by_meal = {}
        for menu in menus:
            if menu.meal_type not in menus_by_meal:
                menus_by_meal[menu.meal_type] = []
            menus_by_meal[menu.meal_type].append(menu)

        # دریافت رزروهای کاربر برای تاریخ هدف
        user_reservations = FreeRestaurantReservation.objects.filter(
            user=request.user,
            reservation_date=target_date
        ).values_list('menu_item_id', flat=True)

        # دریافت موجودی کیف پول
        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        context = {
            'today_date': j_today.strftime('%Y/%m/%d'),
            'selected_day': selected_day,
            'target_date': target_date,
            'menus_by_meal': menus_by_meal,
            'user_reservations': set(user_reservations),
            'wallet_balance': wallet.balance,
            'persian_weekday': persian_weekday,
        }

        return render(request, self.template_name, context)

    def post(self, request):
        menu_id = request.POST.get('menu_id')
        day = request.POST.get('day')

        if not menu_id:
            messages.error(request, "غذای معتبر انتخاب نشده است.")
            return redirect(f"{request.path}?day={day}")

        menu = get_object_or_404(FreeRestaurantMenu, id=menu_id, is_available=True)

        # محاسبه تاریخ هدف
        today = date.today()
        weekday_mapping = {
            'شنبه': 6, 'یک‌شنبه': 0, 'دوشنبه': 1, 'سه‌شنبه': 2,
            'چهارشنبه': 3, 'پنج‌شنبه': 4, 'جمعه': 5
        }
        target_weekday = weekday_mapping.get(day, today.weekday())
        days_ahead = target_weekday - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        target_date = today + timedelta(days=days_ahead)

        # بررسی رزرو تکراری
        if FreeRestaurantReservation.objects.filter(
                user=request.user,
                menu_item=menu,
                reservation_date=target_date
        ).exists():
            messages.warning(request, f"شما قبلاً «{menu.name}» را برای این روز رزرو کرده‌اید.")
            return redirect(f"{request.path}?day={day}")

        # بررسی موجودی کیف پول
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        if wallet.balance < menu.price:
            messages.error(request, f"موجودی کافی ندارید. مبلغ {menu.price:,} تومان نیاز است.")
            return redirect(f"{request.path}?day={day}")

        try:
            with transaction.atomic():
                # ایجاد رزرو
                FreeRestaurantReservation.objects.create(
                    user=request.user,
                    menu_item=menu,
                    reservation_date=target_date,
                    status='reserved'
                )

                # کسر مبلغ از کیف پول
                wallet.balance -= menu.price
                wallet.save()

                # ثبت تراکنش (اختیاری)
                from .models import Transaction
                Transaction.objects.create(
                    user=request.user,
                    transaction_type='reserve',
                    amount=menu.price,
                    balance_after=wallet.balance,
                    description=f'رزرو رستوران آزاد: {menu.name} برای تاریخ {target_date}'
                )

            messages.success(request, f"غذای «{menu.name}» با موفقیت رزرو شد! ✅")
        except Exception as e:
            messages.error(request, "خطا در ثبت رزرو. لطفاً دوباره تلاش کنید.")

        return redirect(f"{request.path}?day={day}")


class WeeklyReservationView(LoginRequiredMixin, View):
    template_name = "menu/weekly_reservation.html"

    def get(self, request):
        # دریافت offset هفته از query parameter
        week_offset = int(request.GET.get("week_offset", 0))

        # محاسبه تاریخ شروع و پایان هفته
        today = date.today()
        start_of_week = (
            today - timedelta(days=today.weekday()) + timedelta(days=week_offset)
        )
        end_of_week = start_of_week + timedelta(days=6)

        # دریافت منوهای فعال برای هفته جاری
        menus = DailyMenu.objects.filter(
            date__range=[start_of_week, end_of_week], is_active=True
        ).order_by("date", "meal_type")

        # گروه‌بندی منوها بر اساس تاریخ
        menus_by_date = []
        current_date = start_of_week

        while current_date <= end_of_week:
            day_menus = [m for m in menus if m.date == current_date]
            if day_menus:
                menus_by_date.append({"date": current_date, "menus": day_menus})
            current_date += timedelta(days=1)

        # دریافت رزروهای کاربر در هفته جاری
        user_reservations = FoodReservation.objects.filter(
            student=request.user,
            meal_date__range=[start_of_week, end_of_week],
            status__in=["pending", "confirmed"],
        )

        # ایجاد دیکشنری برای دسترسی سریع
        reservations_dict = {r.menu_id: r.id for r in user_reservations}

        # محاسبه مجموع کل رزروها
        total_reserved = sum(r.menu.price for r in user_reservations)

        # دریافت موجودی کیف پول
        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        context = {
            "today": today,
            "menus_by_date": menus_by_date,
            "reservations_dict": reservations_dict,
            "wallet_balance": wallet.balance,
            "total_reserved": total_reserved,
            "week_offset": week_offset,
        }

        return render(request, self.template_name, context)

    def post(self, request):
        action = request.POST.get("action")

        if action == "reserve":
            return self.reserve_food(request)
        elif action == "cancel":
            return self.cancel_reservation(request)

        messages.error(request, "عملیات نامعتبر است.")
        return redirect("menu:weekly_reservation")

    def reserve_food(self, request):
        menu_id = request.POST.get("menu_id")

        if not menu_id:
            messages.error(request, "منوی معتبر انتخاب نشده است.")
            return redirect("menu:weekly_reservation")

        menu = get_object_or_404(DailyMenu, id=menu_id, is_active=True)

        # بررسی رزرو تکراری
        if FoodReservation.objects.filter(student=request.user, menu=menu).exists():
            messages.warning(
                request, f"شما قبلاً «{menu.get_meal_type_display()}» را رزرو کرده‌اید."
            )
            return redirect("menu:weekly_reservation")

        # بررسی ظرفیت
        if menu.reserved_count >= menu.capacity:
            messages.error(
                request, f"ظرفیت {menu.get_meal_type_display()} تکمیل شده است."
            )
            return redirect("menu:weekly_reservation")

        # بررسی موجودی کیف پول
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        if wallet.balance < menu.price:
            required_amount = intcomma(menu.price)
            messages.error(
                request, f"موجودی کافی ندارید. مبلغ {required_amount} تومان نیاز است."
            )
            return redirect("menu:weekly_reservation")

        try:
            with transaction.atomic():
                # ایجاد رزرو
                reservation = FoodReservation.objects.create(
                    student=request.user,
                    menu=menu,
                    meal_date=menu.date,
                    status="pending",
                )

                # کسر مبلغ از کیف پول
                wallet.balance -= menu.price
                wallet.save()

                # افزایش تعداد رزروها
                menu.reserved_count += 1
                menu.save()

            success_amount = intcomma(menu.price)
            messages.success(
                request,
                f"{menu.get_meal_type_display()} به مبلغ {success_amount} تومان با موفقیت رزرو شد! ✅",
            )
        except Exception as e:
            messages.error(request, "خطا در ثبت رزرو. لطفاً دوباره تلاش کنید.")

        return redirect("menu:weekly_reservation")

    def cancel_reservation(self, request):
        reservation_id = request.POST.get("reservation_id")

        if not reservation_id:
            messages.error(request, "رزرو معتبر انتخاب نشده است.")
            return redirect("menu:weekly_reservation")

        reservation = get_object_or_404(
            FoodReservation, id=reservation_id, student=request.user
        )

        if reservation.status not in ["pending", "confirmed"]:
            messages.error(request, "این رزرو قابل لغو نیست.")
            return redirect("menu:weekly_reservation")

        if reservation.meal_date < date.today():
            messages.error(request, "نمی‌توانید رزرو روزهای گذشته را لغو کنید.")
            return redirect("menu:weekly_reservation")

        menu = reservation.menu

        try:
            with transaction.atomic():
                # بازگشت مبلغ به کیف پول
                wallet, _ = Wallet.objects.select_for_update().get_or_create(
                    user=request.user
                )
                wallet.balance += menu.price
                wallet.save()

                # حذف رزرو
                reservation.delete()

                # کاهش ظرفیت
                if menu.reserved_count > 0:
                    menu.reserved_count -= 1
                    menu.save()

            refund_formatted = intcomma(menu.price)
            messages.success(
                request,
                f"رزرو {menu.get_meal_type_display()} لغو شد و {refund_formatted} تومان به کیف پول شما بازگشت! 💰",
            )
        except Exception as e:
            messages.error(request, "خطا در لغو رزرو.")

        return redirect("menu:weekly_reservation")


class TransactionsView(LoginRequiredMixin, View):
    template_name = "menu/transactions.html"

    def get(self, request):
        search_query = request.GET.get("q", "")
        page_number = request.GET.get("page", 1)
        transactions = Transaction.objects.filter(user=request.user)

        # جستجو
        if search_query:
            transactions = transactions.filter(
                Q(transaction_type__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(amount__icontains=search_query)
            )

        # صفحه‌بندی
        paginator = Paginator(transactions, 10)  # 10 تراکنش در هر صفحه
        page_obj = paginator.get_page(page_number)

        # محاسبه موجودی فعلی
        if transactions.exists():
            current_balance = transactions.first().balance_after
        else:
            current_balance = 0

        context = {
            "transactions": page_obj,
            "search_query": search_query,
            "current_balance": current_balance,
            "paginator": paginator,
            "page_obj": page_obj,
        }

        return render(request, self.template_name, context)


class WalletChargeView(LoginRequiredMixin, View):
    template_name = "menu/wallet_charge.html"

    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        return render(request, self.template_name, {"wallet": wallet})

    def post(self, request):
        amount = request.POST.get("amount")
        if not amount or not amount.isdigit():
            messages.error(request, "مبلغ وارد شده معتبر نیست.")
            return redirect("menu:wallet_charge")

        amount = int(amount)
        if amount <= 0:
            messages.error(request, "مبلغ باید بیشتر از صفر باشد.")
            return redirect("menu:wallet_charge")

        try:
            with transaction.atomic():
                wallet, _ = Wallet.objects.select_for_update().get_or_create(
                    user=request.user
                )
                wallet.balance += amount
                wallet.save()

                Transaction.objects.create(
                    user=request.user,
                    transaction_type="charge",
                    amount=amount,
                    balance_after=wallet.balance,
                    description=f"شارژ کیف پول به مبلغ {amount:,} تومان",
                )

            messages.success(request, f"مبلغ {amount:,} تومان با موفقیت شارژ شد! 💰")
        except Exception as e:
            messages.error(request, "خطا در شارژ کیف پول.")

        return redirect("menu:wallet_charge")





class ReportsView(LoginRequiredMixin, View):
    template_name = "menu/reports.html"

    def get(self, request):
        # بازه زمانی پیش‌فرض (30 روز اخیر)
        days = int(request.GET.get('days', 30))
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # دریافت کیف پول کاربر
        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        # 1. گزارش تراکنش‌ها
        transactions = Transaction.objects.filter(
            user=request.user,
            created_at__date__range=[start_date, end_date]
        ).order_by('-created_at')

        # 2. گزارش رزروها
        reservations = FoodReservation.objects.filter(
            student=request.user,
            meal_date__range=[start_date, end_date]
        ).select_related('menu').order_by('-meal_date')

        # 3. آمار کلی
        total_charge = Transaction.objects.filter(
            user=request.user,
            transaction_type='charge',
            created_at__date__range=[start_date, end_date]
        ).aggregate(total=Sum('amount'))['total'] or 0

        total_spent = Transaction.objects.filter(
            user=request.user,
            transaction_type='reserve',
            created_at__date__range=[start_date, end_date]
        ).aggregate(total=Sum('amount'))['total'] or 0

        total_refund = Transaction.objects.filter(
            user=request.user,
            transaction_type='refund',
            created_at__date__range=[start_date, end_date]
        ).aggregate(total=Sum('amount'))['total'] or 0

        # 4. آمار رزروها
        total_reservations = reservations.count()
        confirmed_reservations = reservations.filter(status='confirmed').count()
        cancelled_reservations = reservations.filter(status='cancelled').count()

        # 5. گزارش روزانه (آخرین 7 روز)
        daily_stats = []
        for i in range(6, -1, -1):
            day = end_date - timedelta(days=i)
            day_transactions = Transaction.objects.filter(
                user=request.user,
                created_at__date=day
            )

            day_reservations = FoodReservation.objects.filter(
                student=request.user,
                meal_date=day
            )

            daily_stats.append({
                'date': day,
                'transactions': day_transactions.count(),
                'reservations': day_reservations.count(),
                'charge': day_transactions.filter(transaction_type='charge').aggregate(Sum('amount'))[
                              'amount__sum'] or 0,
                'spent': day_transactions.filter(transaction_type='reserve').aggregate(Sum('amount'))[
                             'amount__sum'] or 0,
            })

        # 6. گزارش غذاهای پرطرفدار
        popular_foods = FoodReservation.objects.filter(
            student=request.user,
            meal_date__range=[start_date, end_date]
        ).values(
            'menu__menufooditem__food_item__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        context = {
            'wallet_balance': wallet.balance,
            'transactions': transactions,
            'reservations': reservations,
            'total_charge': total_charge,
            'total_spent': total_spent,
            'total_refund': total_refund,
            'total_reservations': total_reservations,
            'confirmed_reservations': confirmed_reservations,
            'cancelled_reservations': cancelled_reservations,
            'daily_stats': daily_stats,
            'popular_foods': popular_foods,
            'start_date': start_date,
            'end_date': end_date,
            'days': days,
        }

        return render(request, self.template_name, context)





class WeeklyReservationsView(LoginRequiredMixin, View):
    template_name = "menu/weekly_reservations.html"

    def get(self, request):
        week_offset = int(request.GET.get('week_offset', 0))

        today = date.today()
        start_of_week = today - timedelta(days=today.weekday()) + timedelta(days=week_offset)
        end_of_week = start_of_week + timedelta(days=6)

        # ✅ استفاده از prefetch_related برای رابطه ManyToMany
        reservations = FoodReservation.objects.filter(
            student=request.user,
            meal_date__range=[start_of_week, end_of_week],
            status__in=['pending', 'confirmed']
        ).select_related('menu').prefetch_related('menu__menufooditem_set__food_item').order_by('meal_date',
                                                                                                'menu__meal_type')

        total_amount = sum(reservation.menu.price for reservation in reservations)

        from jdatetime import date as jdate
        persian_start = jdate.fromgregorian(date=start_of_week).strftime('%Y/%m/%d')
        persian_end = jdate.fromgregorian(date=end_of_week).strftime('%Y/%m/%d')

        context = {
            'reservations': reservations,
            'total_amount': total_amount,
            'start_date': persian_start,
            'end_date': persian_end,
            'week_offset': week_offset,
            'is_current_week': week_offset == 0,
        }

        return render(request, self.template_name, context)