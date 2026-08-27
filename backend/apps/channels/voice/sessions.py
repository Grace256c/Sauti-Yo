from apps.channels.models import VoiceSession


def get_or_create_session(session_id, phone_number):
    return VoiceSession.objects.get_or_create(
        session_id=session_id,
        defaults={
            "phone_number": phone_number,
            "state": "awaiting_recording",
        },
    )


def update_session(session, **fields):
    for field, value in fields.items():
        setattr(session, field, value)
    session.save()
    return session


def end_session(session):
    return update_session(session, is_active=False, state="ended")
