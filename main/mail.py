from django.core.mail import send_mail
from django.conf import settings
import random

def send_code(to_email, subject):
    # subject = 'Код для регистрации в приложении'
    message = random.randint(100000, 999999)
    full_message = f"От App_for_bg. Код: {message}"
    
    send_mail(
        subject=subject,
        message=full_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        # recipient_list=[settings.SERVER_EMAIL],
        recipient_list=[to_email],
        fail_silently=False,
    )

    return message



