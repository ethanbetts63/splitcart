from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa

def generate_shopping_list_pdf(shopping_plan):
    """
    Generates a PDF for the given shopping plan using an HTML template.
    
    Args:
        shopping_plan (dict): A dictionary representing the shopping plan.
        
    Returns:
        bytes: The generated PDF as a byte string, or None if an error occurred.
    """
    template = get_template('shopping_list_pdf.html')
    context = {'shopping_plan': shopping_plan}
    html = template.render(context)

    result = BytesIO()
    # The encoding must be set to UTF-8 to handle all characters correctly.
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        return result.getvalue()
    
    # In case of an error, you might want to log pdf.err for debugging
    print(f"PDF Generation Error: {pdf.err}")
    return None
