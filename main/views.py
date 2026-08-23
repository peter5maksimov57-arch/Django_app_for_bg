from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from main import forms
from main import models
from main import mail
  
def index(request):
    if request.method == "POST":
        userform = forms.UserForm(request.POST)

        if userform.is_valid():
            email = userform.cleaned_data["email"]
            password = userform.cleaned_data["password"]

            try:
                user = models.Person.objects.get(email=email)

                if check_password(password, user.password):
                    return HttpResponse(f"<h2>Hello, {user.name}</h2>")
                    """сделай приветвие и переход на главную страницу"""
                else:
                    userform.add_error("password", "Неверный пароль.")
                    return render(request, "index.html", {"form": userform})
                """Сделай тож как виджет какой-то или ещё что-то, чтоб потом можно было ещё раз войти"""
            except models.Person.DoesNotExist:
                userform.add_error("email", "Пользователь с таким email не найден.")
                return render(request, "index.html", {"form": userform})
            """Снова придумай что-то"""
            
        else:
            return render(request, "index.html", {"form": userform})
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
                userform.add_error("email", "Пользователь с таким email уже существует.")
                return render(request, "index.html", {"form": userform})
            else:
                request.session['reg_email'] = email
                request.session['reg_name'] = name
                request.session['reg_password'] = password
                # request.session['reg_balance'] = balance
                
                code = mail.send_code(email, 'Код для регистрации в приложении')
                request.session['verification_code'] = str(code)
                return redirect('reg_code')
                # user_code = forms.RegCode(request.POST)
                # code = mail.send_code(email)
                # if user_code.is_valid():
                #     us_code = user_code.cleaned_data['us_code']
                #     if us_code == code:
                #         hash_password = make_password(password)
                #         user = models.Person(
                #             email=email,
                #             name=name,
                #             password=hash_password,
                #             role='',
                #             # age=age,
                #             balance=0
                #             )
                #         user.save()
                #         return HttpResponse(f"<h2>Пользователь {name} добавлен</h2>")
                #         """Сделай вместо пользователь добавлен какой-ниюудь красивый виджет, что добавлен 
                #         и переадресацию на экран входа (index)"""
                #     else:
                #         return HttpResponse("Неверный код")
                #         """Сделай какой-ниюудь виджет или чёт ещё, чтоб просто вылезало про ошибку данных
                #         и пусть заново вводит"""
                # else:
                #     return HttpResponse("Invalid code")
                #     """Сделай какой-ниюудь виджет или чёт ещё, чтоб просто вылезало про ошибку данных
                #     и пусть заново вводит"""
            #     hash_password = make_password(password)
            #     user = models.Person(
            #         email=email,
            #         name=name,
            #         password=hash_password,
            #         role='',
            #         # age=age,
            #         balance=0
            #     )
            #     user.save()
            #     return HttpResponse(f"<h2>Пользователь {name} добавлен</h2>")
            # """Сделай вместо пользователь добавлен какой-ниюудь красивый виджет, что добавлен 
            # и переадресацию на экран входа (index)"""
            
        else:
            return render(request, "index.html", {"form": userform})
            """Сделай какой-ниюудь виджет или чёт ещё, чтоб просто вылезало про ошибку данных
            и пусть заново регается"""
    else:
        userform = forms.RegForm()
        return render(request, "index.html", {"form": userform})
 
def reg_code(request):
    if 'reg_email' not in request.session:
        return HttpResponse("Сессия истекла")
    """Чет добавь и переход на экран входа"""

    if request.method == "POST":
        user_code_form = forms.RegCode(request.POST)
        if not user_code_form.is_valid():
            return render(request, "reg_code.html", {"form": user_code_form})

        user_code = user_code_form.cleaned_data['us_code']
        
        expected_code = request.session.get('verification_code')
        
        if user_code == expected_code:
            email = request.session.get('reg_email')
            name = request.session.get('reg_name')
            password = request.session.get('reg_password')
            # balance = request.session.get('reg_balance', 0)
            
            hash_password = make_password(password)
            
            user = models.Person(
                email=email,
                name=name,
                password=hash_password,
                role='',
                balance=0
            )
            user.save()
            
            request.session.flush()
            return HttpResponse(f"<h2>Пользователь {name} добавлен</h2>")
            """Сделай вместо пользователь добавлен какой-ниюудь красивый виджет, что добавлен 
            и переадресацию на экран входа (index)"""
        # user_code = forms.RegCode(request.POST)
        # code = mail.send_code(email)
        # if user_code.is_valid():
        #     us_code = user_code.cleaned_data['us_code']
        #     if us_code == code:
        #         hash_password = make_password(password)
        #         user = models.Person(
        #             email=email,
        #             name=name,
        #             password=hash_password,
        #             role='',
        #             # age=age,
        #             balance=0
        #             )
        #         user.save()
                # return HttpResponse(f"<h2>Пользователь {name} добавлен</h2>")
                # """Сделай вместо пользователь добавлен какой-ниюудь красивый виджет, что добавлен 
                # и переадресацию на экран входа (index)"""
            # else:
            #     return HttpResponse("Неверный код")
            #     """Сделай какой-ниюудь виджет или чёт ещё, чтоб просто вылезало про ошибку данных
            #         и пусть заново вводит"""
        else:
            user_code_form.add_error('us_code', "Введён неверный код подтверждения.")
            return render(request, "reg_code.html", {"form": user_code_form})
            """Сделай какой-ниюудь виджет или чёт ещё, чтоб просто вылезало про ошибку данных
            и пусть заново вводит"""

    else:
        return render(request, "reg_code.html", {"form": forms.RegCode()})
    """Переделай файл, я занейронил, тут вылезает код еще сам по себе без почты"""


def password_reset(request):
    if request.method == "POST":
        userform = forms.EmailForm(request.POST)
        if userform.is_valid():
            email = userform.cleaned_data['email']
            if models.Person.objects.filter(email=email).exists():
                request.session['res_email'] = email
                code = mail.send_code(email, 'Код для сброса пароля')
                request.session['reset_code'] = str(code)
                return redirect('res_code')
            else:
                userform.add_error('email', "Пользователь с таким email не найден.")
                return render(request, "index.html", {"form": userform})
        else:
            return render(request, "index.html", {"form": userform})
    else:
            userform = forms.EmailForm()
            return render(request, "index.html", {"form": userform})


def res_code(request):
    if 'res_email' not in request.session:
        return HttpResponse("Сессия истекла")
    """Чет добавь и переход на экран входа"""
    if request.method == "POST":
        user_code_form = forms.RegCode(request.POST)
        if not user_code_form.is_valid():
            return render(request, "reg_code.html", {"form": user_code_form})

        user_code = user_code_form.cleaned_data['us_code']
            
        expected_code = request.session.get('reset_code')
            
        if user_code == expected_code:
            return redirect('new_pas')
        else:
            user_code_form.add_error('us_code', "Введён неверный код подтверждения.")
            return render(request, "reg_code.html", {"form": user_code_form})
            """Сделай какой-ниюудь виджет или чёт ещё, чтоб просто вылезало про ошибку данных
            и пусть заново вводит"""
    else:
        return render(request, "reg_code.html", {"form": forms.RegCode()})

    
def new_pas(request):
    if 'res_email' not in request.session:
        return HttpResponse("Сессия истекла")
        """Чет добавь и переход на экран входа"""
    if request.method == "POST":
        userform = forms.PasswordForm(request.POST)
        if userform.is_valid():
            n_password = userform.cleaned_data['password']
            email = request.session.get('res_email')
            user = models.Person.objects.get(email=email)
            hash_password = make_password(n_password)
            user.password = hash_password
            user.save()
            request.session.flush()
            return HttpResponse(f"Пароль изменён")
            """Сделай вместо пользователь добавлен какой-ниюудь красивый виджет, что добавлен 
            и переадресацию на экран входа (index)"""
        else:
            return render(request, "index.html", {"form": userform})
        """Сделай по красоте"""

    else:
        userform = forms.PasswordForm()
        return render(request, "index.html", {"form": userform})
    """Сделай по красоте"""
    
