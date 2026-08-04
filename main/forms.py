from django import forms
 
class UserForm(forms.Form):
    name = forms.CharField(min_length=2, max_length=20)
    age = forms.IntegerField(min_value=1)
    email = forms.EmailField()