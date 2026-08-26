from apps.channels.models import UssdSession


def get_or_create_session(session_id, phone_number):
    return UssdSession.objects.get_or_create(
        session_id=session_id,
        defaults={
            "phone_number": phone_number,
            "state": "language_select",
        },
    )


def update_session(session, **fields):
    for field, value in fields.items():
        setattr(session, field, value)
    session.save()
    return session


def end_session(session):
    return update_session(session, is_active=False)
