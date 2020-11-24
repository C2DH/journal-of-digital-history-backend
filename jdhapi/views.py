from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import mixins, viewsets
from rest_framework import generics
from jdhapi.models import *
from jdhapi.serializers import *
from rest_framework import permissions
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework.response import Response


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'authors':reverse('author-list',request=request, format=format),
        'datasets':reverse('dataset-list',request=request, format=format),
        'abstracts':reverse('abstract-list',request=request, format=format),
    })


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
