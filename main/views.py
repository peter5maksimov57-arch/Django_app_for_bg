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
                request.session['email'] = email
                request.session['name'] = user.name
                # request.session['password'] = user.password
                request.session['balance'] = user.balance
                request.session['role'] = user.role
                request.session['user_id'] = user.id
                if check_password(password, user.password):
                    return render(request, "home.html", {"user": user})

                else:
                    userform.add_error("password", "Неверный пароль.")
                    return render(request, "index.html", {"form": userform})

            except models.Person.DoesNotExist:
                userform.add_error("email", "Пользователь с таким email не найден.")
                return render(request, "index.html", {"form": userform})

            
        else:
            return render(request, "index.html", {"form": userform})
    else:
        userform = forms.UserForm()
        return render(request, "index.html", {"form": userform})
    # userform = UserForm(field_order = ["age", "name"])
    # return render(request, "index.html", {"form": userform})
    # return render(request, "index.html")
    # return HttpResponse("Apl_for_bg")


def main_page(request):
    if request.method == "POST":
        pass
    else:
        pass
        # return render(request, "index.html", {"form": userform})


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
    else:
        userform = forms.RegForm()
        return render(request, "index.html", {"form": userform})
 
def reg_code(request):
    if 'reg_email' not in request.session:
        return render(request, "status.html", {
            "title": "Сессия истекла",
            "message": "Начните регистрацию заново, чтобы получить новый код.",
            "button_text": "Вернуться к регистрации",
            "button_url": "/registration/",
        })

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
            return render(request, "status.html", {
                "title": "Регистрация завершена",
                "message": f"Пользователь {name} успешно добавлен.",
                "button_text": "Перейти ко входу",
                "button_url": "/",
            })

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


    else:
        return render(request, "reg_code.html", {"form": forms.RegCode()})



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
        return render(request, "status.html", {
            "title": "Сессия истекла",
            "message": "Запросите новый код для изменения пароля.",
            "button_text": "Повторить сброс пароля",
            "button_url": "/password_reset/",
        })

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

    else:
        return render(request, "reg_code.html", {"form": forms.RegCode()})

    
def new_pas(request):
    if 'res_email' not in request.session:
        return render(request, "status.html", {
            "title": "Сессия истекла",
            "message": "Запросите новый код для изменения пароля.",
            "button_text": "Повторить сброс пароля",
            "button_url": "/password_reset/",
        })
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
            return render(request, "status.html", {
                "title": "Пароль изменён",
                "message": "Теперь вы можете войти с новым паролем.",
                "button_text": "Перейти ко входу",
                "button_url": "/",
            })

        else:
            return render(request, "index.html", {"form": userform})

    else:
        userform = forms.PasswordForm()
        return render(request, "index.html", {"form": userform})

    
def create_tr(request):
    if 'user_id' not in request.session:
        return HttpResponse("Сессия истекла")
    
    if request.method == "POST":
        userform = forms.CreatTrForm(request.POST)

        if userform.is_valid():
            user_id = request.session['user_id']

            # email = userform.cleaned_data['email']
            amount = userform.cleaned_data['amount']
            type_tr = userform.cleaned_data['type_tr']
            # time = forms.DateTimeField()
            category = userform.cleaned_data['category']
            res_or_sen = userform.cleaned_data['res_or_sen']
            regullar = userform.cleaned_data['regullar']

            if amount <= 0:
                return HttpResponse(f"Транзакция должна быть больше 0")
            """Добавь чёт"""

            try:
                transaction = models.Transaction.new_tr(
                    user_id=user_id,
                    amount=amount,
                    type_tr=type_tr,
                    category=category,
                    res_or_sen=res_or_sen,
                    regullar=regullar
                )
                
                
                user = models.Person.objects.get(id=user_id)
                if type_tr == 'Поступление':
                    user.balance = user.balance + amount
                    user.save()
                else:
                    user.balance = user.balance - amount
                    user.save()
                
                return HttpResponse(f"Транзакция добавлена")
                """Сделай вместо пользователь добавлен какой-ниюудь красивый виджет, что добавлен 
                и переадресацию на экран входа (index)"""
            
            except Exception as e:
                return HttpResponse(f"Ошибка {e}")
            """Добавь чёт"""
            
        else:
            return render(request, "index.html", {"form": userform})
            """Сделай по красоте""" 
    else:
        userform = forms.CreatTrForm()
        return render(request, "index.html", {"form": userform})
        """Сделай по красоте"""
