import africastalking
from django.conf import settings

_sms_service = None


def _get_sms_service():
    global _sms_service
    if _sms_service is None:
        africastalking.initialize(
            settings.AFRICASTALKING_USERNAME,
            settings.AFRICASTALKING_API_KEY,
        )
        _sms_service = africastalking.SMS
    return _sms_service


def send_sms(phone_number, message, short_code=None, link_id=None):
    """
    Send an SMS through Africa's Talking.

    When short_code and link_id are supplied, reply through the two-way
    shortcode using the premium/on-demand SMS API. Otherwise fall back to
    the normal outbound SMS API.
    """
    sms_service = _get_sms_service()

    if short_code and link_id:
        return sms_service.send_premium(
            message,
            short_code,
            [phone_number],
            link_id=link_id,
        )

    sender_id = settings.AFRICASTALKING_SMS_SENDER_ID or None
    return sms_service.send(
        message,
        [phone_number],
        sender_id=sender_id,
    )
