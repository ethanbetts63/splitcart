from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa
from .get_image_base64 import get_image_base64


def generate_shopping_list_pdf(export_data):
    """
    Generates a PDF for the given shopping plan using an HTML template.
    """
    shopping_plan = export_data.get('shopping_plan', {})
    # Process images and calculate subtotals
    for store, plan in shopping_plan.items():
        subtotal = 0
        for item in plan.get('items', []):
            item['image_base64'] = get_image_base64(item.get('image_url'))
            subtotal += item.get('price', 0) * item.get('quantity', 0)
        plan['subtotal'] = subtotal  # Add subtotal to the plan dictionary

    template = get_template('shopping_list_pdf.html')
    context = {'export_data': export_data}
    html = template.render(context)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        return result.getvalue()
    
    print(f"PDF Generation Error: {pdf.err}")
    return None