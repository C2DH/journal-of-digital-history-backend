from jdhapi.models import *
from jdhapi.serializers import *
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser


#SERIALIZATION

author1 = Author(lastname='Carmada', firstname='Sandra', affiliation='C2DH')
author1.save()
author2= Author(lastname='Guido', firstname='Daniele',affiliation='C2DH')
author2.save()
abstract1= Abstract(title='ÉISCHTE WELTKRICH: REMEMBERING THE GREAT WAR IN LUXEMBOURG - DIGITAL EXHIBITION', abstract='The digital exhibition Éischte Weltkrich: Remembering the Great War in Luxembourg is a project currently developed by the C2DH - Centre for Contemporary and Digital History of the University of Luxembourg with the objective of addressing a neglected and understudied period in the history of the Grand Duchy. Supported by the Ministry of State and bringing together the collections and expertise of all the major Luxembourgish museums, archives and cultural institutions, the project has progressively deepened and widened its scope, aspiring to become a long-term online resource. This paper outlines the exhibition concept and design, describing the process of development and implementation of the website, the challenges in dealing with a variety of sources from different repositories and the possible solutions for addressing a wider audience with accessible and engaging content using a wide range of multimedia features and new strategies in digital storytelling.', contact_lastname='guerard', contact_firstname='elisabeth',contact_affiliation='c2dh',contact_email='eliselavy@gmail.com',contact_orcid='0000-0002-0795-3467',consented= True, status='Submitted')
abstract1.save()
abstract1.authors.add(author1)
abstract1.authors.add(author2)
serializer = AbstractSerializer(abstract1)
#serializer.data
content = JSONRenderer().render(serializer.data)
content


snippet = Dataset(url='https://github.com/C2DH/statec-exhibit', description='description3')
snippet.save()
snippet = Dataset(url='https://github.com/C2DH/dariah-campus', description='description2')
snippet.save()

serializer = DatasetSerializer(snippet)



import io 
stream = io.BytesIO(content)
data = JSONParser().parse(stream)
serializer = DatasetSerializer(data = data)
serializer.is_valid()

serializer = DatasetSerializer(Dataset.objects.all(), many=True)
data = serializer.data
serializer = DatasetSerializer(data = data)
serializer.is_valid()

serializer = AuthorSerializer(Author.objects.filter(lastname='Carmada'),many=True)
serializer.data






dataset = DatasetSerializer(Dataset.objects.filter(description='description1'), many=True)



author = AuthorSerializer(Author.objects.filter(lastname='Carmada'),many=True) 



#CREATE AN INSTANCE
snippet = Dataset(url='https://github.com/C2DH/statec-exhibit', description='EXEMPLE serialization - deserialization') 
snippet.save() 
#SERIALIZE 
serializer = DatasetSerializer(snippet)
#TO FINALIZE THE SERIALIZATION PROCESS WE RENDER THE DATA INTO json
content = JSONRenderer().render(serializer.data) 
#DESERIALIZATION IS SIMILAR
stream = io.BytesIO(content)
data = JSONParser().parse(stream)
serializer = DatasetSerializer(data=data)
serializer.is_valid()
#RESTORE THOSE NATIVE DATATYPES INTO A FULLY POPULATED OBJECT INSTANCE
serializer.validated_data
serializer.save()

snippet = Author(lastname='serial', firstname='deserial', affiliation='C2DH', email='',orcid='')
snippet.save() 
serializer = AuthorSerializer(snippet)
content = JSONRenderer().render(serializer.data) 
stream = io.BytesIO(content)
data = JSONParser().parse(stream)
serializer = AuthorSerializer(data=data)
serializer.is_valid()
serializer.validated_data
serializer.save()


abstract1= Abstract(title='Digital exhibition', abstract='The digital exhibition Éischte Weltkrich: Remembering the Great War in Luxembourg is a project currently developed by the C2DH - Centre for Contemporary and Digital History of the University of Luxembourg with the objective of addressing a neglected and understudied period in the history of the Grand Duchy. Supported by the Ministry of State and bringing together the collections and expertise of all the major Luxembourgish museums, archives and cultural institutions, the project has progressively deepened and widened its scope, aspiring to become a long-term online resource. This paper outlines the exhibition concept and design, describing the process of development and implementation of the website, the challenges in dealing with a variety of sources from different repositories and the possible solutions for addressing a wider audience with accessible and engaging content using a wide range of multimedia features and new strategies in digital storytelling.', contact_lastname='guerard', contact_firstname='elisabeth',contact_affiliation='c2dh',contact_email='eliselavy@gmail.com',contact_orcid='0000-0002-0795-3467',consented= True, status='Submitted')
abstract1.save() 
serializer = AbstractSerializer(abstract1)
content = JSONRenderer().render(serializer.data) 
stream = io.BytesIO(content)
data = JSONParser().parse(stream)
serializer = AbstractSerializer(data=data)
serializer.is_valid()
serializer.validated_data


abstract = AbstractSerializer(Abstract.objects.filter(contact_lastname='guerard'),many=True)
content = JSONRenderer().render(abstract.data) 
stream = io.BytesIO(content)
data = JSONParser().parse(stream)
serializer = AbstractSerializer(data=data)
serializer.is_valid()
serializer.validated_data

------------------------
#With the ModelSerializer

from jdhapi.serializers import *
serializer = AuthorSerializer()
print(repr(serializer))


from jdhapi.serializers import *
serializer = DatasetSerializer()
print(repr(serializer))