from django.urls import path

from menu import views
from menu.views import (
    FreeRestaurantView,
    ReportsView,
    TransactionsView,
    WalletChargeView,
    WeeklyReservationView, WeeklyReservationsView,
)

app_name = "menu"

urlpatterns = [
    path("menu/", views.MenuView.as_view(), name="menu"),
    path("sale-day/", views.SaleDayView.as_view(), name="sale_day"),
    path(
        "cancel-reservation/<int:reservation_id>/",
        views.CancelReservationView.as_view(),
        name="cancel_reservation",
    ),
    path("freerestaurant/", FreeRestaurantView.as_view(), name="free_restaurant"),
    path(
        "weekly-reservation/",
        WeeklyReservationView.as_view(),
        name="weekly_reservation",
    ),
    path("transactions/", TransactionsView.as_view(), name="transactions"),
    path("wallet/charge/", WalletChargeView.as_view(), name="wallet_charge"),
    path("reports/", ReportsView.as_view(), name="reports"),
    path('weekly-reservations/', WeeklyReservationsView.as_view(), name='weekly_reservations')
]
