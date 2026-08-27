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


def send_sms(phone_number, message):
    """
    Sends an SMS via Africa's Talking. Returns the SDK's response dict.
    Raises on failure - callers are responsible for handling/logging.
    """
    sms_service = _get_sms_service()
    sender_id = settings.AFRICASTALKING_SMS_SENDER_ID or None
    return sms_service.send(message, [phone_number], sender_id=sender_id)
