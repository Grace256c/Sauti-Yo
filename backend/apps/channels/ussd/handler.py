from . import menus, sessions

MAX_INVALID_ATTEMPTS = 3


def handle_ussd_request(session_id, phone_number, text):
    session, created = sessions.get_or_create_session(session_id, phone_number)

    if created:
        response_text, ended = menus.render_state(session.state, session)
        sessions.update_session(session, is_active=not ended)
        return _format_response(response_text, ended)

    user_input = text.split("*")[-1] if text else ""
    result = menus.transition_state(session.state, session, user_input)

    if result is None:
        attempts = session.context.get("attempts", 0) + 1
        if attempts >= MAX_INVALID_ATTEMPTS:
            sessions.end_session(session)
            return _format_response(
                menus.get_copy("ussd.too_many_invalid", session.language), True
            )
        sessions.update_session(
            session, context={**session.context, "attempts": attempts}
        )
        response_text, ended = menus.render_state(session.state, session)
        invalid_prefix = menus.get_copy("ussd.invalid_choice", session.language)
        return _format_response(f"{invalid_prefix}\n{response_text}", ended)

    next_state, next_context = result
    session.state = next_state
    session.context = next_context
    response_text, ended = menus.render_state(next_state, session)
    sessions.update_session(
        session,
        state=next_state,
        context=next_context,
        language=session.language,
        is_active=not ended,
    )
    return _format_response(response_text, ended)


def _format_response(text, ended):
    prefix = "END " if ended else "CON "
    return f"{prefix}{text}"
