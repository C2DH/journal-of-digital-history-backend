import logging
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics
from jdhapi.models import Abstract
from jdhapi.models import Author
from jdhapi.models import Dataset
from jdhapi.serializers import CreateAbstractSerializer
from jdhapi.serializers import AbstractSerializer
from jdhapi.serializers import AuthorSerializer
from jdhapi.serializers import DatasetSerializer
from rest_framework import permissions
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from drf_recaptcha.fields import ReCaptchaV2Field
from rest_framework.serializers import Serializer
from django.core.mail import send_mail
from jdh.validation import JSONSchema
from jsonschema.exceptions import SchemaError
from jsonschema.exceptions import ValidationError


document_json_schema = JSONSchema(filepath='submit-abstract.json')
logger = logging.getLogger(__name__)


def getDefaultBody(subject):
    defaultBody = "Dear author, your submission " + subject + " has been sent to the managing editor of the Journal of Digital History. We will contact you back in a few days to discuss the feasibility of your article, as the JDH's layered articles imply to publish an hermeneutics and a data layer." +  "\n" + "Best regard, the JDH team."
    return defaultBody


def sendmailAbstractReceived(subject, sent_to):
    body = getDefaultBody(subject)
    try:
        send_mail(
            subject,
            body,
            'jdh.admin@uni.lu',
            [sent_to,'jdh.admin@uni.lu'],
            fail_silently=False,
        )
    except Exception as e:
        print(e)


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'authors': reverse('author-list', request=request, format=format),
        'datasets': reverse('dataset-list', request=request, format=format),
        'abstracts': reverse('abstract-list', request=request, format=format),
    })


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def SubmitAbstract(request):
    try:
        document_json_schema.validate(instance=request.data)
    except ValidationError as err:
        logger.exception(err)
        return Response({
            'error': 'ValidationError',
            'message': err.message
        }, status=status.HTTP_400_BAD_REQUEST)
    except SchemaError as err:
        logger.exception(err)
        return Response({
            'error': 'SchemaError',
            'message': err.message
        }, status=status.HTTP_400_BAD_REQUEST)
    logger.info('submit abstract validated.')
    contact = request.data.get("contact")
    abstract = Abstract(
        title=request.data.get("title"),
        abstract=request.data.get("abstract"),
        contact_orcid=contact.get("orcid"),
        contact_affiliation=contact.get("affiliation"),
        contact_email=contact.get("email"),
        contact_lastname=contact.get("lastname"),
        contact_firstname=contact.get("firstname"),
        consented=request.data.get("acceptConditions")
    )
    abstract.save()
    authors = request.data.get('authors', [])
    for author in authors:
        new_author = Author(
            lastname=author['lastname'],
            firstname=author['firstname'],
            email=author['email'],
            affiliation=author['affiliation'],
            orcid=author['orcid']
        )
        new_author.save()
        abstract.authors.add(new_author)
    datasets = request.data.get('datasets', [])
    for dataset in datasets:
        new_dataset = Dataset(
            url=dataset['url'],
            description=dataset['description']
        )
        new_dataset.save()
        abstract.datasets.add(new_dataset)
    logger.info("End submit abstract")
    # Send an email of confirmation
    sendmailAbstractReceived(abstract.title, abstract.contact_email)
    serializer = AbstractSerializer(abstract)
    return Response(serializer.data)


class V2Serializer(Serializer):
    token = ReCaptchaV2Field()


class AuthorList(generics.ListCreateAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

class AuthorDetail(generics.RetrieveUpdateDestroyAPIView):
    # TO UPDATE OR DELETE need to be authenticated
    #permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class DatasetList(generics.ListCreateAPIView):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer

class DatasetDetail(generics.RetrieveUpdateDestroyAPIView):
    # TO UPDATE OR DELETE need to be authenticated
    #permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer


class AbstractList(generics.ListCreateAPIView):
    queryset = Abstract.objects.all()
    serializer_class = AbstractSerializer




    @csrf_exempt
    def create(self, request, *args, **kwargs):
        serializer = V2Serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        self.serializer_class = CreateAbstractSerializer
        super().create(request, *args, **kwargs)
        return Response({'received data': request.data})




class AbstractDetail(generics.RetrieveUpdateDestroyAPIView):
    # TO UPDATE OR DELETE need to be authenticated
    #permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Abstract.objects.all()
    serializer_class = AbstractSerializer


"""
class AuthorList(mixins.ListModelMixin, mixins.CreateModelMixin,generics.GenericAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

    def get(self,request, *args, **kwargs):
        return self.list(request,*args,**kwargs)

    def post(self,request, *args, **kwargs):
        return self.create(request,*args,**kwargs)


class AuthorDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,generics.GenericAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

    def get(self,request, *args, **kwargs):
        return self.retrieve(request,*args,**kwargs)

    def put(self,request, *args, **kwargs):
        return self.update(request,*args,**kwargs)

    def delete(self,request, *args, **kwargs):
        return self.destroy(request,*args,**kwargs)



class AuthorList(APIView):

    def get(self,request, format=None):
        authors = Author.objects.all()
        serializer = AuthorSerializer(authors, many=True)
        return Response(serializer.data)

    def post(self,request, format=None):
        serializer = AuthorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)

class AuthorDetail(APIView):

    def get_object(self, pk):
        try:
            return Author.objects.get(pk=pk)
        except Author.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        author = self.get_object(pk)
        serializer = AuthorSerializer(author)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        author = self.get_object(pk)
        serializer = AuthorSerializer(author, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        author = self.get_object(pk)
        author.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


 @api_view(['GET','POST'])
def author_list(request, format=None):
    if request.method == 'GET':
        authors = Author.objects.all()
        serializer = AuthorSerializer(authors, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = AuthorSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.data,status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET','PUT', 'DELETE'])
def author_detail(request, pk,format=None):
    try:
        author = Author.objects.get(pk=pk)
    except Author.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = AuthorSerializer(author)
        return Response(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = AuthorSerializer(snippet, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        author.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
 """
