from django.http import HttpResponse
from django.shortcuts import render
from main.forms import UserForm
  
def index(request):
    if request.method == "POST":
        userform = UserForm(request.POST)
        if userform.is_valid():
            name = userform.cleaned_data["name"]
            return HttpResponse(f"<h2>Hello, {name}</h2>")
        else:
            return HttpResponse("Invalid data")
    else:
        userform = UserForm()
        return render(request, "index.html", {"form": userform})
    # userform = UserForm(field_order = ["age", "name"])
    # return render(request, "index.html", {"form": userform})
    # return render(request, "index.html")
    # return HttpResponse("Apl_for_bg")

def about(request):
    return HttpResponse("О сайте")
 
def contact(request):
    return HttpResponse("Контакты")