from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q
from django.db import transaction
from smtplib import SMTPException
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
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
                if check_password(password, user.password):
                    request.session.cycle_key()
                    request.session['user_id'] = user.id
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


def main_page(request, member_id=None):
    account_user = models.Person.objects.filter(id=request.session.get('user_id')).first()
    if account_user is None:
        request.session.pop('user_id', None)
        return render(request, "status.html", {
            "title": "Сессия истекла",
            "message": "Войдите в аккаунт",
            "button_text": "Войти",
            "button_url": "/",
        })

    user = account_user
    if member_id is not None:
        if member_id == account_user.id:
            return redirect('main_page')
        if not models.Dependence.objects.filter(
            user_id_admin=account_user.id, user_id_sub=member_id
        ).exists():
            return render(request, "status.html", {
                "title": "Доступ запрещён",
                "message": "Просматривать статистику участника может только администратор его семьи.",
                "button_text": "Вернуться к семье",
                "button_url": reverse('family'),
            }, status=403)
        user = models.Person.objects.filter(id=member_id).first()
        if user is None:
            return render(request, "status.html", {
                "title": "Участник не найден",
                "message": "Этот профиль больше недоступен.",
                "button_text": "Вернуться к семье",
                "button_url": reverse('family'),
            }, status=404)

    viewing_member = user.id != account_user.id
    dashboard_url = (
        reverse('family_member', kwargs={'member_id': user.id})
        if viewing_member else reverse('main_page')
    )

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
                                        "account_user": account_user,
                                        "viewing_member": viewing_member,
                                        "dashboard_url": dashboard_url,
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


def family_page(request):
    account_user = models.Person.objects.filter(id=request.session.get('user_id')).first()
    if account_user is None:
        return main_page(request)

    # Каждая семья определяется существующими связями с её администратором.
    admin_ids = set(models.Dependence.objects.filter(
        Q(user_id_admin=account_user.id) | Q(user_id_sub=account_user.id)
    ).values_list('user_id_admin', flat=True))
    links = list(models.Dependence.objects.filter(user_id_admin__in=admin_ids))
    people = models.Person.objects.in_bulk(
        admin_ids | {link.user_id_sub for link in links}
    )
    family_groups = []
    for admin_id in sorted(admin_ids, key=lambda value: (value != account_user.id, value)):
        if admin_id not in people:
            continue
        member_ids = {
            link.user_id_sub for link in links
            if link.user_id_admin == admin_id and link.user_id_sub != admin_id
        }
        family_groups.append({
            'admin': people[admin_id],
            'members': sorted(
                (people[pk] for pk in member_ids if pk in people),
                key=lambda person: (person.name.casefold(), person.id),
            ),
            'can_view': admin_id == account_user.id,
        })
    return render(request, "family.html", {
        'account_user': account_user,
        'family_groups': family_groups,
        'can_create_family': not any(group['can_view'] for group in family_groups),
    })


def family_create(request):
    account_user = models.Person.objects.filter(id=request.session.get('user_id')).first()
    if account_user is None:
        return main_page(request)

    is_family_admin = models.Dependence.objects.filter(user_id_admin=account_user.id).exists()

    now = timezone.now().timestamp()
    invitation = request.session.get('family_invitation')
    if invitation and (
        invitation['admin_id'] != account_user.id or now >= invitation['expires_at']
    ):
        request.session.pop('family_invitation', None)
        invitation = None

    form_data = request.POST.copy() if request.method == 'POST' else None
    if form_data is not None and form_data.get('action') == 'send':
        form_data['code'] = ''
    form = forms.FamilyInviteForm(
        form_data,
        initial={'email': invitation['email']} if invitation else None,
    )
    notice = ''
    if request.method == 'POST' and form.is_valid():
        action = request.POST.get('action')
        email = form.cleaned_data['email']
        recipients = list(models.Person.objects.filter(email__iexact=email)[:2])
        recipient = recipients[0] if len(recipients) == 1 else None
        if recipient is None:
            form.add_error('email', 'Укажите почту существующего профиля с уникальным адресом.')
        elif recipient.id == account_user.id:
            form.add_error('email', 'Нельзя пригласить самого себя.')
        elif models.Dependence.objects.filter(
            user_id_admin=account_user.id, user_id_sub=recipient.id
        ).exists():
            form.add_error('email', 'Этот пользователь уже состоит в вашей семье.')
        elif action == 'send':
            last_sent = request.session.get('family_invitation_sent_at', 0)
            if now - last_sent < 60:
                form.add_error(None, 'Повторное приглашение можно отправить через минуту.')
            else:
                try:
                    code = mail.send_family_code(recipient.email, account_user.name)
                except (SMTPException, OSError):
                    form.add_error(None, 'Не удалось отправить письмо. Попробуйте позже.')
                else:
                    invitation = {
                        'admin_id': account_user.id, 'member_id': recipient.id,
                        'email': recipient.email, 'code_hash': make_password(code),
                        'expires_at': now + 600, 'attempts': 0,
                    }
                    request.session['family_invitation'] = invitation
                    request.session['family_invitation_sent_at'] = now
                    notice = 'Код отправлен получателю. Он действует 10 минут.'
        elif action == 'confirm':
            if not invitation:
                form.add_error('code', 'Сначала отправьте приглашение. Если код истёк, запросите новый.')
            elif (invitation['member_id'] != recipient.id
                  or invitation['email'].casefold() != email.casefold()):
                form.add_error('email', 'Этот код выдан для другого адреса. Отправьте новое приглашение.')
            elif not form.cleaned_data['code']:
                form.add_error('code', 'Введите код из письма получателя.')
            elif not check_password(form.cleaned_data['code'], invitation['code_hash']):
                invitation['attempts'] += 1
                if invitation['attempts'] >= 5:
                    request.session.pop('family_invitation', None)
                    invitation = None
                    form.add_error('code', 'Попытки закончились. Отправьте новое приглашение.')
                else:
                    request.session['family_invitation'] = invitation
                    form.add_error('code', 'Неверный код приглашения.')
            else:
                with transaction.atomic():
                    models.Dependence.add_dependence(account_user.id, recipient.id)
                request.session.pop('family_invitation', None)
                return redirect('family')
        else:
            form.add_error(None, 'Выберите отправку приглашения или подтверждение кода.')

    return render(request, 'family_create.html', {
        'account_user': account_user, 'form': form, 'notice': notice,
        'is_family_admin': is_family_admin,
        'invitation_email': invitation['email'] if invitation else '',
    })


@require_POST
def family_unlink(request, member_id=None, admin_id=None):
    account_user = models.Person.objects.filter(id=request.session.get('user_id')).first()
    if account_user is None:
        return main_page(request)

    leaving = member_id is None
    if leaving:
        member_id = account_user.id
    else:
        admin_id = account_user.id
    # При удалении администратор берётся из сессии, при выходе - сам участник.
    if admin_id == member_id or not models.Dependence.objects.filter(
        user_id_admin=admin_id, user_id_sub=member_id
    ).exists():
        return render(request, 'status.html', {
            'title': 'Действие недоступно',
            'message': 'Нет прав на изменение этой семьи или участник уже вышел из неё.',
            'button_text': 'Вернуться к семье', 'button_url': reverse('family'),
        }, status=403)

    with transaction.atomic():
        models.Dependence.delete_dependence(admin_id, member_id)
    request.session.pop('family_invitation', None)
    messages.success(request, 'Вы вышли из семьи.' if leaving else 'Участник удалён из семьи.')
    return redirect('family')


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
