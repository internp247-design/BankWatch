from django import forms
from .models import Rule, RuleCondition, CustomCategory, CustomCategoryRule, CustomCategoryRuleCondition
from django.forms import inlineformset_factory

class RuleForm(forms.ModelForm):
    class Meta:
        model = Rule
        fields = ['name', 'category', 'rule_type', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Paytm IRCTC Bookings'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'rule_type': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class RuleConditionForm(forms.ModelForm):
    class Meta:
        model = RuleCondition
        fields = [
            'condition_type', 
            'keyword', 'keyword_match_type',
            'amount_operator', 'amount_value', 'amount_value2',
            'date_start', 'date_end',
            'source_channel'
        ]
        widgets = {
            'condition_type': forms.Select(attrs={
                'class': 'form-control condition-type-select',
            }),
            'keyword': forms.TextInput(attrs={
                'class': 'form-control keyword-field',
                'placeholder': 'Enter keyword (e.g., Paytm, IRCTC)'
            }),
            'keyword_match_type': forms.Select(attrs={'class': 'form-control keyword-field'}),
            'amount_operator': forms.Select(attrs={'class': 'form-control amount-field'}),
            'amount_value': forms.NumberInput(attrs={
                'class': 'form-control amount-field',
                'placeholder': 'Amount',
                'step': '0.01'
            }),
            'amount_value2': forms.NumberInput(attrs={
                'class': 'form-control amount-field',
                'placeholder': 'To amount (for between)',
                'step': '0.01'
            }),
            'date_start': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control date-field'
            }),
            'date_end': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control date-field'
            }),
            'source_channel': forms.Select(attrs={'class': 'form-control source-field'}),
        }

# Create formset for multiple conditions
RuleConditionFormSet = inlineformset_factory(
    Rule, 
    RuleCondition, 
    form=RuleConditionForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


# ============= CUSTOM CATEGORY FORMS =============

class CustomCategoryForm(forms.ModelForm):
    class Meta:
        model = CustomCategory
        fields = ['name', 'description', 'color', 'icon', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Entertainment Subscriptions'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Optional: Describe this category',
                'rows': 3
            }),
            'color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control',
                'style': 'height: 40px; cursor: pointer;'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., fa-film, fa-shopping-bag, fa-heart'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CustomCategoryRuleForm(forms.ModelForm):
    class Meta:
        model = CustomCategoryRule
        fields = ['name', 'rule_type', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Netflix & Streaming Services'
            }),
            'rule_type': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'checked': True}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set is_active to True by default for new instances
        if not self.instance.pk:
            self.fields['is_active'].initial = True


class CustomCategoryRuleConditionForm(forms.ModelForm):
    class Meta:
        model = CustomCategoryRuleCondition
        fields = [
            'condition_type', 
            'keyword', 'keyword_match_type',
            'amount_operator', 'amount_value', 'amount_value2',
            'date_start', 'date_end',
        ]
        widgets = {
            'condition_type': forms.Select(attrs={
                'class': 'form-control condition-type-select',
            }),
            'keyword': forms.TextInput(attrs={
                'class': 'form-control keyword-field',
                'placeholder': 'Enter keyword (e.g., Netflix, Spotify)'
            }),
            'keyword_match_type': forms.Select(attrs={'class': 'form-control keyword-field'}),
            'amount_operator': forms.Select(attrs={'class': 'form-control amount-field'}),
            'amount_value': forms.NumberInput(attrs={
                'class': 'form-control amount-field',
                'placeholder': 'Amount',
                'step': '0.01'
            }),
            'amount_value2': forms.NumberInput(attrs={
                'class': 'form-control amount-field',
                'placeholder': 'To amount (for between)',
                'step': '0.01'
            }),
            'date_start': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control date-field'
            }),
            'date_end': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control date-field'
            }),
        }


# Create formset for custom category rule conditions
CustomCategoryRuleConditionFormSet = inlineformset_factory(
    CustomCategoryRule, 
    CustomCategoryRuleCondition, 
    form=CustomCategoryRuleConditionForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)