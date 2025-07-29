from django_filters.rest_framework import DjangoFilterBackend
from django.views.decorators.csrf import csrf_exempt
from drf_recaptcha.fields import ReCaptchaV2Field
from jdhapi.models import Abstract
from jdhapi.serializers.abstract import CreateAbstractSerializer, AbstractSlimSerializer
from rest_framework import permissions, generics, filters
from rest_framework.response import Response
from rest_framework.serializers import Serializer


class V2Serializer(Serializer):
    token = ReCaptchaV2Field()


class AbstractList(generics.ListCreateAPIView):
    queryset = Abstract.objects.all()
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AbstractSlimSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = [
        "id",
        "pid",
        "title",
        "callpaper",
        "callpaper__title",
        "submitted_date",
        "validation_date",
        "language_preference",
        "contact_affiliation",
        "contact_lastname",
        "contact_firstname",
        "consented",
        "authors",
    ]
    ordering_fields = [
        "id",
        "title",
        "callpaper",
        "callpaper__title",
        "submitted_date",
        "validation_date",
        "status",
        "contact_lastname",
        "contact_firstname",
        "contact_affiliation",
    ]
    search_fields = [
        "title",
        "pid",
        "contact_lastname",
        "contact_firstname",
    ]

    def get_queryset(self):
        queryset = Abstract.objects.all()
        status_param = self.request.query_params.get("status")

        qs = super().filter_queryset(queryset)

        if status_param:
            if status_param.startswith("!"):
                status_value = status_param[1:]
                qs = qs.exclude(status=status_value)
            else:
                qs = qs.filter(status=status_param)

        return qs

    @csrf_exempt
    def create(self, request, *args, **kwargs):
        serializer = V2Serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        self.serializer_class = CreateAbstractSerializer
        super().create(request, *args, **kwargs)
        return Response({"received data": request.data})


class AbstractDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Abstract.objects.all()
    serializer_class = AbstractSlimSerializer
    lookup_field = "pid"
