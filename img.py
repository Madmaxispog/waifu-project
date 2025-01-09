import time
import PIL
from PIL import Image
import requests
import io

API_URL = "https://api-inference.huggingface.co/models/cagliostrolab/animagine-xl-3.0"
headers = {"Authorization": "Bearer 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"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    try:
        response.raise_for_status()
    except requests.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}') 
    except Exception as err:
        print(f'Other error occurred: {err}')
    else:
        print('Request to API was successful!')

    print(f"Response status code: {response.status_code}")
    print(f"Response content type: {response.headers['content-type']}")
    return response.content

negativeprompt = "(best quality), (high quality:1.4), (color), (living), (natural fingers:1.2), (style: anime), (composition: close-up), (lighting: natural light), (beautiful), (well-proportioned), (attractive), (pleasing to the eye), (aesthetically pleasing), (harmonious), (balanced), (in focus), (high resolution), (realistic), (well-drawn), (perfect anatomy), (healthy), (natural), (pleasant), (appealing), (charming), (graceful), (elegant), (refined), (sophisticated), (detailed), (realistic textures), (smooth shading), (dynamic lighting), (volumetric effects), (naturalistic poses)"

def generate_image(user_input, negativeprompt):
    image_bytes = query({"inputs": f"{user_input} {negativeprompt}"})
    print("Image generation model is currently loading..")
    while b"loading" in image_bytes:
        time.sleep(5)
        image_bytes = query({"inputs": f"{user_input} {negativeprompt}"})
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image = image.convert("RGB")
        image = image.resize((512, 512), Image.LANCZOS)
    except PIL.UnidentifiedImageError as err:
        print(f"Error opening image: {err}")
        return None

    return image
