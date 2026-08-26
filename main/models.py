from django.db import models
from django.utils import timezone
 
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


    # @property
    # def categories(self):
    #     categories = ["Переводы людям", "Зарплата", "Продукты", "Электроника",
    #         "Развлечения", "Кафе и рестораны", "Товары для дома", "АЗС", "Цифровые сервисы",
    #         "Пополнение наличными", "Одежда и обувь", "ЖКХ", "Другое"]
    #     return categories


    def __str__(self):
        return f'{self.type_tr} суммы {self.amount} пользователя {self.user_id}'


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

