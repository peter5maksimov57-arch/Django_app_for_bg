from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from calendar import monthrange
from datetime import date
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
                # request.session['email'] = email
                # request.session['name'] = user.name
                # request.session['password'] = user.password
                # request.session['balance'] = user.balance
                # request.session['role'] = user.role
                request.session['user_id'] = user.id
                if check_password(password, user.password):
                    # return render(request, "home.html", {"user": user})
                    return redirect('main_page')

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
    if 'user_id' not in request.session:
        return render(request, "status.html", {
            "title": "Сессия истекла",
            "message": "Войдите в аккаунт",
            "button_text": "Войти",
            "button_url": "/",
        })

    user = models.Person.objects.get(id=request.session['user_id'])

    view_form = forms.ViewTrForm()

    all_transactions = models.Transaction.objects.filter(user_id=user.id).order_by('-time')

    # try:
    #     user = models.Person.objects.get(id=request.session['user_id'])
    # except models.Person.DoesNotExist:
    #     request.session.flush()
    #     return render(request, "status.html", {
    #         "title": "Ошибка",
    #         "message": "Пользователь не найден. Пожалуйста, войдите снова.",
    #         "button_text": "Войти",
    #         "button_url": "/",
    #     })

    if request.method == "POST" and 'refresh_chart' not in request.POST:
        view_form = forms.ViewTrForm(request.POST)

        if view_form.is_valid():
            # email = userform.cleaned_data['email']
            # amount = userform.cleaned_data['amount']
            type_tr = view_form.cleaned_data['type_tr']
            # time = forms.DateTimeField()
            category = view_form.cleaned_data['category']
            res_or_sen = view_form.cleaned_data['res_or_sen']
            regullar = view_form.cleaned_data['regullar']
        
            filters = {'type_tr': type_tr,
                        'category': category,
                        'res_or_sen': res_or_sen,
                        'regullar': regullar,
                        }
        
            all_transactions = models.Transaction.all_transactions(user.id, filters)

    income = models.Transaction.all_typeTr_for_month(user.id, 'Поступление')
    outcome = models.Transaction.all_typeTr_for_month(user.id, 'Трата')

    inc_for_categories = models.Transaction.inc_for_categories(user.id)

    chart_colors = ['#4f6500', '#7b940d', '#a2c41d', '#d2fa3e',
                    '#efb82f', '#e78132', '#c5523b', '#8f3c52',
                    '#635080', '#39758a', '#3d8d70', '#70a947', '#aacb55']
    expense_chart = []
    chart_segments = []
    chart_position = 0

    if outcome > 0:
        for index, (category, amount) in enumerate(inc_for_categories):
            segment_end = chart_position + amount / outcome * 100
            color = chart_colors[index % len(chart_colors)]
            chart_segments.append(
                f'{color} {chart_position:.2f}% {segment_end:.2f}%'
            )
            expense_chart.append({
                'category': category,
                'amount': amount,
                'color': color,
            })
            chart_position = segment_end

    expense_chart_gradient = (
        f"conic-gradient({', '.join(chart_segments)})"
        if chart_segments else '#e8f5d0'
    )

    # Данные для вкладки общей статистики за выбранный месяц.
    try:
        selected_year, selected_month = map(
            int, request.GET.get('month', '').split('-', 1)
        )
        selected_date = date(selected_year, selected_month, 1)
    except (TypeError, ValueError):
        today = timezone.localdate()
        selected_date = date(today.year, today.month, 1)

    month_transactions = models.Transaction.objects.filter(
        user_id=user.id,
        time__year=selected_date.year,
        time__month=selected_date.month,
    )
    days_in_month = monthrange(selected_date.year, selected_date.month)[1]
    daily_income = [0.0] * days_in_month
    daily_expenses = [0.0] * days_in_month
    month_categories = {}

    for transaction in month_transactions:
        transaction_time = transaction.time
        if timezone.is_aware(transaction_time):
            transaction_time = timezone.localtime(transaction_time)
        day_index = transaction_time.day - 1

        if transaction.type_tr == 'Трата':
            daily_expenses[day_index] += transaction.amount
            month_categories[transaction.category] = (
                month_categories.get(transaction.category, 0) + transaction.amount
            )
        elif transaction.type_tr == 'Поступление':
            daily_income[day_index] += transaction.amount

    analytics_income = sum(daily_income)
    analytics_expenses = sum(daily_expenses)
    month_categories = sorted(
        month_categories.items(), key=lambda item: item[1], reverse=True
    )

    analytics_expense_chart = []
    analytics_segments = []
    analytics_position = 0
    if analytics_expenses > 0:
        for index, (category, amount) in enumerate(month_categories):
            segment_end = analytics_position + amount / analytics_expenses * 100
            color = chart_colors[index % len(chart_colors)]
            analytics_segments.append(
                f'{color} {analytics_position:.2f}% {segment_end:.2f}%'
            )
            analytics_expense_chart.append({
                'category': category,
                'amount': amount,
                'color': color,
            })
            analytics_position = segment_end

    analytics_expense_gradient = (
        f"conic-gradient({', '.join(analytics_segments)})"
        if analytics_segments else '#e8f5d0'
    )

    plot_left, plot_right = 58, 950
    plot_top, plot_bottom = 24, 292
    chart_maximum = max(daily_income + daily_expenses + [1])

    def build_points(values):
        points = []
        for index, amount in enumerate(values):
            x = plot_left + index * (plot_right - plot_left) / max(days_in_month - 1, 1)
            y = plot_bottom - amount / chart_maximum * (plot_bottom - plot_top)
            points.append({
                'x': f'{x:.1f}',
                'y': f'{y:.1f}',
                'day': index + 1,
                'amount': amount,
            })
        return points

    income_points = build_points(daily_income)
    expense_points = build_points(daily_expenses)
    y_ticks = [
        {
            'y': f'{plot_bottom - ratio * (plot_bottom - plot_top):.1f}',
            'amount': chart_maximum * ratio,
        }
        for ratio in (0, 0.25, 0.5, 0.75, 1)
    ]
    x_ticks = [
        point for point in income_points
        if point['day'] == 1
        or point['day'] == days_in_month
        or point['day'] % 5 == 0
    ]

    month_number = selected_date.year * 12 + selected_date.month - 1
    previous_number = month_number - 1
    next_number = month_number + 1
    previous_month = date(
        previous_number // 12, previous_number % 12 + 1, 1
    )
    next_month = date(next_number // 12, next_number % 12 + 1, 1)
    month_names = (
        'январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
        'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь'
    )

    last_tr = models.Transaction.last_transaction(user.id)

    future_tr = models.Transaction.future_transaction(user.id)

    # print(future_tr)



    form = forms.CreatTrForm()
    return render(request, "home.html", {"user": user, 
                                        "form": form,
                                        "view_form": view_form,
                                        "all_transactions": all_transactions,
                                        "income": income,
                                        "outcome": outcome,
                                        "top_categories": inc_for_categories[:3],
                                        "inc_for_categories": inc_for_categories,
                                        "expense_chart": expense_chart,
                                        "expense_chart_gradient": expense_chart_gradient,
                                        "last_tr": last_tr[:3],
                                        "future_tr": future_tr,
                                        "analytics_month_label": f"{month_names[selected_date.month - 1]} {selected_date.year}",
                                        "analytics_previous_month": previous_month.strftime('%Y-%m'),
                                        "analytics_next_month": next_month.strftime('%Y-%m'),
                                        "analytics_income": analytics_income,
                                        "analytics_expenses": analytics_expenses,
                                        "analytics_expense_chart": analytics_expense_chart,
                                        "analytics_expense_gradient": analytics_expense_gradient,
                                        "analytics_income_points": income_points,
                                        "analytics_expense_points": expense_points,
                                        "analytics_income_polyline": ' '.join(f"{point['x']},{point['y']}" for point in income_points),
                                        "analytics_expense_polyline": ' '.join(f"{point['x']},{point['y']}" for point in expense_points),
                                        "analytics_y_ticks": y_ticks,
                                        "analytics_x_ticks": x_ticks})


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
        return render(request, "status.html", {
            "title": "Сессия истекла",
            "message": "Войдите в аккаунт.",
            "button_text": "Войти",
            "button_url": "/",
        })
    
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
                
                messages.success(request, 'Транзакция успешно добавлена!')
                return redirect('main_page')
            
            except Exception as e:
                return render(request, "home.html", {
                    "user": models.Person.objects.get(id=user_id),
                    "error": f"Ошибка при создании транзакции: {e}",
                    "form": userform
                })
            
        else:
            user = models.Person.objects.get(id=request.session['user_id'])
            return render(request, "home.html", {
                "user": user,
                "form": userform,
                # "transactions": models.Transaction.objects.filter(user_id=user.id).order_by('-time')
            }) 
    else:
        return redirect('main_page')
    

def logout_view(request):
    request.session.flush()
    return render(request, "status.html", {
        "title": "Выход из аккаунта",
        "message": f"Вы успешно вышли из системы!",
        "button_text": "Перейти ко входу",
        "button_url": "/",
    })


# def view_transactions(request):
#     if 'user_id' not in request.session:
#             return render(request, "status.html", {
#                 "title": "Сессия истекла",
#                 "message": "Войдите в аккаунт.",
#                 "button_text": "Войти",
#                 "button_url": "/",
#             })

#     if request.method == "POST":
#         userform = forms.ViewTrForm(request.POST)
    
#         if userform.is_valid():
#             user_id = request.session['user_id']
    
#             # email = userform.cleaned_data['email']
#             # amount = userform.cleaned_data['amount']
#             type_tr = userform.cleaned_data['type_tr']
#             # time = forms.DateTimeField()
#             category = userform.cleaned_data['category']
#             res_or_sen = userform.cleaned_data['res_or_sen']
#             regullar = userform.cleaned_data['regullar']

#             filters = {'type_tr': type_tr,
#                        'category': category,
#                        'res_or_sen': res_or_sen,
#                        'regullar': regullar,
#                        }

#             transactions = models.Transaction.all_transactions(user_id, filters)
#             # print(transactions)
    
                
                
#         else:
#             user = models.Person.objects.get(id=request.session['user_id'])
#             return render(request, "home.html", {
#                 "user": user,
#                 "form": userform,
#                 # "transactions": models.Transaction.objects.filter(user_id=user.id).order_by('-time')
#             }) 
#     else:
#         return redirect('main_page')
