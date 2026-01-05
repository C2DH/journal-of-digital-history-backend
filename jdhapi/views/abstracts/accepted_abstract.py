from django_filters.rest_framework import DjangoFilterBackend
from jdhapi.models import Abstract, Article
from jdhapi.serializers.abstract import AbstractSerializer
from rest_framework import generics, filters


class AcceptedAbstractList(generics.ListCreateAPIView): 
    queryset = Abstract.objects.all()
    serializer_class = AbstractSerializer
    filter_backends = [
        DjangoFilterBackend
    ]
    filterset_fields = [
        "id", 
        "pid",
        "title",
        "callpaper__title",
        "submitted_date",
        "contact_lastname",
        "contact_firstname"
    ]

    def get_queryset(self): 
        accepted_abstracts_with_cfp = Abstract.objects.filter(status='ACCEPTED', callpaper__isnull=False )
        abstracts_not_written = Article.objects.filter(status='PUBLISHED' or 'TECHNICAL_REVIEW' or 'PEER_REVIEW' or 'DESIGN_REVIEW')
        
        return accepted_abstracts_with_cfp.exclude(pid__in=abstracts_not_written.values_list('abstract__pid', flat=True))

    
    