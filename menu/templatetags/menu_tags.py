# menu/templatetags/menu_tags.py
from django import template

from reservation.models import FoodReservation

register = template.Library()


@register.simple_tag
def get_reservation_id(user, menu_id):
    """
    پیدا کردن reservation_id برای یک کاربر و منو
    """
    try:
        reservation = FoodReservation.objects.get(
            student=user, menu_id=menu_id, status__in=["pending", "confirmed"]
        )
        return reservation.id
    except FoodReservation.DoesNotExist:
        return None
