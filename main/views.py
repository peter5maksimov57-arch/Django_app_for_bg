from django.http import HttpResponse
from django.shortcuts import render
from main import forms
from main import models
  
def index(request):
    if request.method == "POST":
        userform = forms.UserForm(request.POST)
        if userform.is_valid():
            name = userform.cleaned_data["name"]
            return HttpResponse(f"<h2>Hello, {name}</h2>")
        else:
            return HttpResponse("Invalid data")
    else:
        userform = forms.UserForm()
        return render(request, "index.html", {"form": userform})
    # userform = UserForm(field_order = ["age", "name"])
    # return render(request, "index.html", {"form": userform})
    # return render(request, "index.html")
    # return HttpResponse("Apl_for_bg")

def registration(request):
    if request.method == "POST":
        userform = forms.RegForm(request.POST)
        if userform.is_valid():
            email = userform.cleaned_data['email']
            name = userform.cleaned_data["name"]
            # age = userform.cleaned_data['age']
            password = userform.cleaned_data['password']
            # balance = userform.cleaned_data['balance']
            # role = userform.cleaned_data['role']
            if models.Person.objects.filter(email=email).exists():
                return HttpResponse(f"Пользователь с таким email уже есть")
            else:
                user = models.Person(
                    email=email,
                    name=name,
                    password=password,
                    role='',
                    # age=age,
                    balance=0
                )
                user.save()
                return HttpResponse(f"<h2>Пользователь {name} добавлен</h2>")
            """Сделай вместо пользователь добавлен какой-ниюудь красивый виджет, что добавлен 
            и переадресацию на экран входа (index)"""
            
        else:
            return HttpResponse("Invalid data")
            """Сделай какой-ниюудь виджет или чёт ещё, чтоб просто вылезало про ошибку данных
            и пусть заново регается"""
    else:
        userform = forms.RegForm()
        return render(request, "index.html", {"form": userform})
 
def contact(request):
    return HttpResponse("Контакты")