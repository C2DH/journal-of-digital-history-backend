http http://127.0.0.1:8000/api/authors/


http http://127.0.0.1:8000/api/authors/  Accept:application/json #Request JSON

http http://127.0.0.1:8000/api/authors/  Accept:application/html #Request HTML

http http://127.0.0.1:8000/api/authors.json   # JSON suffix

http http://127.0.0.1:8000/api/authors.api     # Browsable API suffix

# POST using form data  doesn't work
http --json POST http://127.0.0.1:8000/api/authors/ lastname="Schafer" firstname="Valérie" orcid="0000-0002-8204-1265" affiliation="C2DH"


# POST using json data work
http --json POST http://127.0.0.1:8000/api/authors/ lastname="Guerard" firstname="Mathieu"  affiliation="C2DH"


""" (base) MacBook-Pro:jdhbackend elisabeth.guerard$ http --json POST http://127.0.0.1:8000/api/authors/ lastname="Guerard" firstname="Mathieu"  affiliation="C2DH"
HTTP/1.1 403 Forbidden
Allow: GET, POST, HEAD, OPTIONS
Content-Length: 58
Content-Type: application/json
Date: Mon, 23 Nov 2020 16:57:57 GMT
Referrer-Policy: same-origin
Server: WSGIServer/0.2 CPython/3.7.6
Vary: Accept, Cookie
X-Content-Type-Options: nosniff
X-Frame-Options: DENY

{
    "detail": "Authentication credentials were not provided."
} """

# POST using json data work with authentification
http --json -a root:root POST http://127.0.0.1:8000/api/authors/ lastname="Guerard" firstname="Mathieu"  affiliation="C2DH"