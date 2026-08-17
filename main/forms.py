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
    