import re

def clean_value(value):
    if value is None:
        return ''
    words = sorted(str(value).lower().split())
    sorted_string = ' '.join(words)
    cleaned_value = re.sub(r'[^a-z0-9]', '', sorted_string)
    return cleaned_value