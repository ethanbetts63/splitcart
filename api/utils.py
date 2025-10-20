from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa
import base64
import requests

def get_image_base64(url):
    """Downloads an image and returns it as a Base64 encoded data URI."""
    if not url:
        return None
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        content_type = response.headers.get('content-type', 'image/jpeg')
        encoded_string = base64.b64encode(response.content).decode('utf-8')
        return f"data:{content_type};base64,{encoded_string}"
    except (requests.exceptions.RequestException, KeyError):
        return None

def generate_shopping_list_pdf(shopping_plan):
    """
    Generates a PDF for the given shopping plan using an HTML template.
    """
    # Process images before rendering the template
    for store, plan in shopping_plan.items():
        for item in plan.get('items', []):
            item['image_base64'] = get_image_base64(item.get('image_url'))

    template = get_template('shopping_list_pdf.html')
    context = {'shopping_plan': shopping_plan}
    html = template.render(context)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        return result.getvalue()
    
    print(f"PDF Generation Error: {pdf.err}")
    return None
