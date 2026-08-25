from rest_framework import generics

from .models import SupportService
from .serializers import SupportServiceSerializer


class SupportServiceListAPIView(generics.ListAPIView):
    serializer_class = SupportServiceSerializer

    def get_queryset(self):
        return SupportService.objects.filter(
            is_active=True
        ).order_by("name")


class SupportServiceDetailAPIView(generics.RetrieveAPIView):
    serializer_class = SupportServiceSerializer
    queryset = SupportService.objects.filter(is_active=True)