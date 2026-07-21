from django.http import HttpResponse
from django.shortcuts import render
  
def index(request):
    return render(request, "index.html")
    # return HttpResponse("Apl_for_bg")

def about(request):
    return HttpResponse("О сайте")
 
def contact(request):
    return HttpResponse("Контакты")