from django import forms

types = (("Vše", "Vše"),
         ("3060", "3060"),
         ("3060 Ti", "3060 Ti"),
         ("3070", "3070"),
         ("3070 Ti", "3070 Ti"),
         ("3080", "3080"),
         ("3080 Ti", "3080 Ti"),
         ("3090", "3090"))


class GputypeForm(forms.Form):
    Model = forms.ChoiceField(choices=types, widget=forms.RadioSelect(attrs={"onChange": 'form.submit()'}))
