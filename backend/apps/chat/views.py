from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import build_chat_response


class ChatAPIView(APIView):
    def post(self, request):
        message = request.data.get("message", "")
        language = request.data.get("language", "en")
        situation_slug = request.data.get(
            "situation_slug"
        )

        result = build_chat_response(
            message=message,
            language=language,
            situation_slug=situation_slug,
        )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )