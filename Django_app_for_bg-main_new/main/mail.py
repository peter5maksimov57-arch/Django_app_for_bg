from django.core.mail import send_mail
from django.conf import settings
import random
import secrets


def send_family_code(to_email, admin_name):
    code = str(secrets.randbelow(900000) + 100000)
    sent = send_mail(
        subject="Приглашение в семью - App_for_bg",
        message=(
            f"Пользователь {admin_name} приглашает вас в семью.\n\n"
            f"Код приглашения: {code}\nКод действует 10 минут.\n\n"
            "После подтверждения отправитель станет администратором семьи "
            "и сможет просматривать ваш баланс, доходы, расходы и операции. "
            "Передайте ему этот код только если согласны вступить в семью. "
            "Если приглашение неожиданное, просто проигнорируйте письмо."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )
    if sent != 1:
        raise OSError("Приглашение не отправлено")
    return code

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


