from django.shortcuts import render
from django.http import HttpResponse, FileResponse
from .models import Greeting
import requests
import os

# Create your views here.
def index(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "index.html")

def test(request):
    r = requests.get('http://httpbin.org/status/418')
    return HttpResponse('<pre>' + r.text + '</pre> <a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/418">ERROR 418, I AM A TEAPOT</a>')

def about(request):
    return render(request, "about.html")

def chesspng(request,piece):
    return FileResponse(open("chess/static/chess/javascript/chessboardjs-1.0.0/img/chesspieces/wikipedia/"+piece+".png","rb"))


def db(request):

    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, "db.html", {"greetings": greetings})
