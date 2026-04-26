from django import forms

class OrderForm(forms.Form):
    coupon_code = forms.CharField(max_length=50, required=False, label="Coupon Code")