from rest_framework import generics

from .models import ChannelContent
from .serializers import ChannelContentSerializer


class ChannelContentListAPIView(generics.ListAPIView):
    serializer_class = ChannelContentSerializer

    def get_queryset(self):
        queryset = ChannelContent.objects.filter(
            is_active=True
        )

        content_key = self.request.query_params.get(
            "content_key"
        )
        language = self.request.query_params.get(
            "language"
        )
        channel = self.request.query_params.get(
            "channel"
        )

        if content_key:
            queryset = queryset.filter(
                content_key=content_key
            )

        if language:
            queryset = queryset.filter(
                language=language
            )

        if channel:
            queryset = queryset.filter(
                channel=channel
            )

        return queryset.order_by(
            "content_key",
            "language",
            "channel",
        )


class ChannelContentDetailAPIView(
    generics.RetrieveAPIView
):
    serializer_class = ChannelContentSerializer
    queryset = ChannelContent.objects.filter(
        is_active=True
    )