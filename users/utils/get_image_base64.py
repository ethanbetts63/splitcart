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