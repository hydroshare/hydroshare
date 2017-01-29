from django import forms


class VariableValidationForm(forms.Form):
    VARIABLE_TYPES = (
        ('Char', 'Char'),  # 8-bit byte that contains uninterpreted character data
        ('Byte', 'Byte'),  # integer(8bit)
        ('Short', 'Short'),  # signed integer (16bit)
        ('Int', 'Int'),  # signed integer (32bit)
        ('Float', 'Float'),  # floating point (32bit)
        ('Double', 'Double'),  # floating point(64bit)
        ('Int64', 'Int64'),  # integer(64bit)
        ('Unsigned Byte', 'Unsigned Byte'),
        ('Unsigned Short', 'Unsigned Short'),
        ('Unsigned Int', 'Unsigned Int'),
        ('Unsigned Int64', 'Unsigned Int64'),
        ('String', 'String'),  # variable length character string
        ('User Defined Type', 'User Defined Type'),  # compound, vlen, opaque, enum
        ('Unknown', 'Unknown')
    )
    name = forms.CharField(max_length=100)
    unit = forms.CharField(max_length=100)
    type = forms.ChoiceField(choices=VARIABLE_TYPES)
    shape = forms.CharField(max_length=100)
    descriptive_name = forms.CharField(max_length=1000, required=False)
    method = forms.CharField(max_length=1000, required=False)
    missing_value = forms.CharField(max_length=100, required=False)
