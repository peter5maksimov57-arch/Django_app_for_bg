from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
 
class Person(models.Model):
    name = models.CharField(max_length=20)
    # age = models.IntegerField()
    email = models.EmailField()
    password = models.CharField(max_length=20)
    balance = models.FloatField()
    role = models.CharField()


    # @property
    # def get_balance(self):
    #     return self.balance


    def __str__(self):
        return self.name



class Transaction(models.Model):
    user_id = models.IntegerField()
    amount = models.FloatField()
    type_tr = models.CharField()
    time = models.DateTimeField()
    category = models.CharField()
    res_or_sen = models.CharField()
    regullar = models.BooleanField()


    categories = ["Переводы людям", "Зарплата", "Продукты", "Электроника",
            "Развлечения", "Кафе и рестораны", "Товары для дома", "АЗС", "Цифровые сервисы",
            "Пополнение наличными", "Одежда и обувь", "ЖКХ", "Другое"]


    def __str__(self):
        return f'{self.type_tr} суммы {self.amount} по категории {self.category} {self.time} {self.res_or_sen}'


    @staticmethod
    def new_tr(user_id, amount, type_tr, category, res_or_sen, regullar=False):
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            type_tr=type_tr,
            category=category,
            res_or_sen=res_or_sen,
            regullar=regullar,
            time=timezone.now()
        )
        transaction.save()
        return transaction


    @staticmethod
    def all_typeTr_for_month(us_id, type_tr):
        now = timezone.now()
        year = now.year
        month = now.month 
        tr = Transaction.objects.filter(user_id=us_id, type_tr=type_tr,
                                        time__year=year, time__month=month)
        income_sum = 0
        for i in tr:
            income_sum += i.amount
        return income_sum


    # @staticmethod
    # def inc_for_categories(us_id):
    #     now = timezone.now()
    #     year = now.year
    #     month = now.month

    #     res = []

    #     for i in Transaction.categories:
    #         tr = Transaction.objects.filter(user_id=us_id, type_tr='Трата',
    #                                         time__year=year, time__month=month, category=i)
    #         summa = sum(j.amount for j in tr)

    #         res.append([i, summa])
    #     res.sort(key=lambda x: x[1], reverse=True)
    #     return res


    @staticmethod
    def inc_for_categories(us_id):
        now = timezone.now()
        year = now.year
        month = now.month

        transactions = Transaction.objects.filter(user_id=us_id, type_tr='Трата',
            time__year=year, time__month=month)
        
        categories_data = {}
        for transaction in transactions:
            if transaction.category not in categories_data:
                categories_data[transaction.category] = 0
            categories_data[transaction.category] += transaction.amount
        
        sorted_categories = sorted(categories_data.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_categories


    @staticmethod
    def last_transaction(us_id):
        last_tr = Transaction.objects.filter(user_id=us_id).order_by('-time')
        # last_tr = [i for i in tr].sort(reverse=True)

        # transactions.sort(reverse=True)
        # transactions = sorted(transactions, reverse=True)
        return last_tr


    @staticmethod
    def future_transaction(user_id, days_ahead=7):
        reg_tr = Transaction.objects.filter(user_id=user_id, regullar=True).order_by('time')
        
        future_tr = []
        today = timezone.now().date()
        
        for transaction in reg_tr:
            last_trans = Transaction.objects.filter(
                user_id=user_id,
                category=transaction.category,
                type_tr=transaction.type_tr,
                amount=transaction.amount,
                regullar=True).order_by('-time').first()
            
            if last_trans:
                last_date = last_trans.time.date()
                next_date = last_date + timedelta(days=30)
            else:
                next_date = today + timedelta(days=1)
            
            days_until = (next_date - today).days
            
            if 0 <= days_until <= days_ahead:
                future_tr.append({
                    'id': transaction.id,
                    'category': transaction.category,
                    'amount': transaction.amount,
                    'type_tr': transaction.type_tr,
                    'res_or_sen': transaction.res_or_sen,
                    'next_date': next_date,
                    'days_left': days_until,
                    'is_regular': True,
                    'status': 'soon' if days_until <= 3 else 'upcoming'
                })
        
        future_tr.sort(key=lambda x: x['next_date'])
        
        return future_tr
        