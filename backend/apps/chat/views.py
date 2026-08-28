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

        result = build_chat_response(
            message=message,
            language=language,
        )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )