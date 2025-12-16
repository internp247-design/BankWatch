from django import forms
from django.core.exceptions import ValidationError
import os
from .models import BankAccount, BankStatement

class BankStatementForm(forms.ModelForm):
    class Meta:
        model = BankStatement
        fields = ['account', 'statement_file']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-control'}),
            'statement_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.xlsx,.xls,.csv'
            }),
        }
    
    def clean_statement_file(self):
        file = self.cleaned_data.get('statement_file')
        if file:
            # Check file size (10MB limit)
            if file.size > 10 * 1024 * 1024:  # 10MB
                raise ValidationError('File size must be less than 10MB.')
            
            # Check file extension
            ext = os.path.splitext(file.name)[1].lower()
            valid_extensions = ['.pdf', '.xlsx', '.xls', '.csv']
            if ext not in valid_extensions:
                raise ValidationError('Unsupported file type. Please upload PDF, Excel, or CSV files.')
        
        return file