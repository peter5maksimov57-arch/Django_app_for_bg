from django import forms
 
class UserForm(forms.Form):
    # name = forms.CharField(min_length=2, max_length=20)
    # age = forms.IntegerField(min_value=1)
    email = forms.EmailField()
    password = forms.CharField(min_length=6, max_length=20)


class RegForm(forms.Form):
    name = forms.CharField(min_length=2, max_length=20)
    # age = forms.IntegerField(min_value=1)
    email = forms.EmailField()
    password = forms.CharField(min_length=6, max_length=20)


class RegCode(forms.Form):
    us_code = forms.CharField(min_length=6, max_length=6)


class EmailForm(forms.Form):
    email = forms.EmailField()

class PasswordForm(forms.Form):
    password = forms.CharField(min_length=6, max_length=20)


class CreatTrForm(forms.Form):
    TYPE_CHOICES = [
        ('Поступление', 'Поступление'),
        ('Трата', 'Трата'),
    ]
    
    CATEGORY_CHOICES = [
        ('Переводы людям', 'Переводы людям'),
        ('Зарплата', 'Зарплата'),
        ('Продукты', 'Продукты'),
        ('Электроника', 'Электроника'),
        ('Развлечения', 'Развлечения'),
        ('Кафе и рестораны', 'Кафе и рестораны'),
        ('Товары для дома', 'Товары для дома'),
        ('АЗС', 'АЗС'),
        ('Цифровые сервисы', 'Цифровые сервисы'),
        ('Пополнение наличными', 'Пополнение наличными'),
        ('Одежда и обувь', 'Одежда и обувь'),
        ('ЖКХ', 'ЖКХ'),
        ('Другое', 'Другое'),
    ]

    # user_id = forms.IntegerField()
    amount = forms.FloatField(min_value=0.01)
    type_tr = forms.ChoiceField(choices=TYPE_CHOICES)
    # time = forms.DateTimeField()
    category = forms.ChoiceField(choices=CATEGORY_CHOICES)
    res_or_sen = forms.CharField()
    regullar = forms.BooleanField(required=False)


class ViewTrForm(forms.Form):
    TYPE_CHOICES = [
        ('Все', 'Все'),
        ('Поступление', 'Поступление'),
        ('Трата', 'Трата'),
    ]
        
    CATEGORY_CHOICES = [
        ('Все', 'Все'),
        ('Переводы людям', 'Переводы людям'),
        ('Зарплата', 'Зарплата'),
        ('Продукты', 'Продукты'),
        ('Электроника', 'Электроника'),
        ('Развлечения', 'Развлечения'),
        ('Кафе и рестораны', 'Кафе и рестораны'),
        ('Товары для дома', 'Товары для дома'),
        ('АЗС', 'АЗС'),
        ('Цифровые сервисы', 'Цифровые сервисы'),
        ('Пополнение наличными', 'Пополнение наличными'),
        ('Одежда и обувь', 'Одежда и обувь'),
        ('ЖКХ', 'ЖКХ'),
        ('Другое', 'Другое'),
    ]

    REGULLAR_CHOICES = [
        ('Все', 'Все'),
        ('Регулярный', 'Регулярный'),
        ('Нерегулярный', 'Нерегулярный'),
    ]


    type_tr = forms.ChoiceField(choices=TYPE_CHOICES)
    # time = forms.DateTimeField()
    category = forms.ChoiceField(choices=CATEGORY_CHOICES)
    res_or_sen = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Все"}),
    )
    regullar = forms.ChoiceField(choices=REGULLAR_CHOICES)
