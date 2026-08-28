from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .services import build_chat_response


class ChatRateThrottle(AnonRateThrottle):
    scope = "chat"


class ChatAPIView(APIView):
    throttle_classes = [ChatRateThrottle]

    def post(self, request):
        message = request.data.get("message", "")
        if not isinstance(message, str):
            message = ""

        language = request.data.get("language", "en")
        if not isinstance(language, str):
            language = "en"

        situation_slug = request.data.get("situation_slug")
        if not isinstance(situation_slug, str):
            situation_slug = None

        result = build_chat_response(
            message=message,
            language=language,
            situation_slug=situation_slug,
        )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )
