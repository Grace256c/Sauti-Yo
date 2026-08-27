import logging

import requests
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def transcribe_recording(recording_url):
    """
    Downloads the call recording from Africa's Talking and transcribes it
    with OpenAI's Whisper API. Returns the transcript text, or None on
    any failure (missing config, empty URL, download error, API error,
    timeout, or an empty result) - every failure mode degrades to "no
    transcript" identically, matching apps.channels.sms.ai_classifier's
    everything-degrades-to-None discipline, so the caller can always
    safely fall back to the not-understood path.
    """
    if not settings.OPENAI_API_KEY or not recording_url:
        return None

    try:
        download = requests.get(recording_url, timeout=10)
        download.raise_for_status()
    except requests.RequestException:
        logger.warning("Voice recording download failed", exc_info=True)
        return None

    try:
        client = _get_client()
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=("recording.mp3", download.content),
            timeout=10.0,
        )
    except Exception:
        # Any failure (auth, rate limit, network, timeout, malformed
        # response, unexpected SDK error) degrades to "no transcript" -
        # this call must never crash the voice handler.
        logger.warning("Voice recording transcription failed", exc_info=True)
        return None

    text = (response.text or "").strip()
    return text or None
