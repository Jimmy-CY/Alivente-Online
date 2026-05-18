"""
Recipe-import helpers: file text extraction + AI structured extraction.

Four pure helper functions (no views, no decorators) supporting the
`import_recipe` / `preview_imported_recipe` views in crud:

File text extraction:
    extract_text_from_pdf(file)    - PyPDF2 page-by-page text extract.
    extract_text_from_docx(file)   - python-docx paragraph extract.
    extract_text_from_image(file)  - PIL Image -> PNG base64, ready
                                     for Claude vision input.

AI structured extraction:
    extract_recipe_with_ai(content, file_type)
        Calls Anthropic Claude with a structured-output prompt to
        parse recipe text or an image into a dict with recipe_name,
        servings, prep/cook/total time, ingredients[] (each with
        quantity/measurement/ingredient/preparation), and
        instructions[]. Retries up to 3 times with backoff (3s, 6s).
        Returns None on persistent failure.

Currently uses claude-sonnet-4-20250514. Update via the model string
in extract_recipe_with_ai when migrating to a newer model.

Extracted from pages/views/main.py as part of the modular views
migration (### RECIPE MANAGEMENT ### -> recipes/ sub-package, phase 4).

Cleanups during the move:
  - Hoisted inline `import time` and `import traceback` from inside
    extract_recipe_with_ai's retry loop / exception handler to
    module-level imports.
  - Removed a stale "Replace the extract_recipe_with_ai function
    in your views.py" comment that dated from an earlier migration.
"""

import base64
import json
import time
import traceback
from io import BytesIO

import anthropic
import PyPDF2
from docx import Document
from PIL import Image

from django.conf import settings


# ============================================
# FILE EXTRACTION FUNCTIONS
# ============================================

def extract_text_from_pdf(file):
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")


def extract_text_from_docx(file):
    """Extract text from Word document"""
    try:
        doc = Document(file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        raise Exception(f"Error reading Word document: {str(e)}")


def extract_text_from_image(file):
    """For images, we'll pass directly to Claude's vision API"""
    # Convert to base64 for Claude API
    try:
        image = Image.open(file)
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        return img_base64
    except Exception as e:
        raise Exception(f"Error processing image: {str(e)}")


# ============================================
# AI EXTRACTION FUNCTION
# ============================================

def extract_recipe_with_ai(content, file_type):
    """Use Claude AI to extract recipe data with structured ingredients"""

    # Get API key from settings
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
    if not api_key:
        raise Exception("ANTHROPIC_API_KEY not found in settings")

    client = anthropic.Anthropic(api_key=api_key)

    # Updated prompt for structured ingredient extraction
    system_prompt = """You are a recipe extraction expert. Extract recipe information from the provided content and return it in JSON format.

Extract the following fields:
- recipe_name: The name of the recipe
- description: A brief description (if available)
- prep_time: Preparation time in minutes (number only)
- cook_time: Cooking time in minutes (number only)
- total_time: Total time in minutes (number only)
- servings: Number of servings (number only)
- ingredients: Array of ingredient objects with these fields:
  * quantity: The amount (e.g., "2", "1/4", "1.5") - extract the number only
  * measurement: The unit (e.g., "cups", "tablespoons", "teaspoons", "packets", "cloves") - use singular lowercase
  * ingredient: The ingredient name (e.g., "flour", "olive oil", "frozen artichokes")
  * preparation: Any preparation notes (e.g., "chopped", "diced", "minced", "grated") - empty string if none
- instructions: Array of instruction strings (step by step)

For ingredients, parse each one carefully:
Example: "2 packets Frozen Artichokes" should be:
  {"quantity": "2", "measurement": "packets", "ingredient": "Frozen Artichokes", "preparation": ""}

Example: "1/4 teaspoon salt" should be:
  {"quantity": "1/4", "measurement": "teaspoon", "ingredient": "salt", "preparation": ""}

Example: "2 tablespoons olive oil, extra virgin" should be:
  {"quantity": "2", "measurement": "tablespoons", "ingredient": "olive oil", "preparation": "extra virgin"}

Example: "1 teaspoon minced fresh garlic" should be:
  {"quantity": "1", "measurement": "teaspoon", "ingredient": "fresh garlic", "preparation": "minced"}

Return ONLY valid JSON with these fields. If a field is not found, use null for numbers or empty string/array for text."""

    for attempt in range(3):
        try:
            if file_type in ['jpg', 'jpeg', 'png']:
                message = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": f"image/{file_type}",
                                        "data": content,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": "Extract the recipe information from this image and return it in the JSON format specified."
                                }
                            ],
                        }
                    ],
                    system=system_prompt
                )
            else:
                message = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    messages=[
                        {
                            "role": "user",
                            "content": f"Extract the recipe information from this text and return it in the JSON format specified:\n\n{content}"
                        }
                    ],
                    system=system_prompt
                )

            # Parse the response
            response_text = message.content[0].text

            # Extract JSON from response (Claude might wrap it in markdown)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            recipe_data = json.loads(response_text)

            # Validate and set defaults
            recipe_data.setdefault('recipe_name', 'Imported Recipe')
            recipe_data.setdefault('description', '')
            recipe_data.setdefault('prep_time', None)
            recipe_data.setdefault('cook_time', None)
            recipe_data.setdefault('total_time', None)
            recipe_data.setdefault('servings', 4)
            recipe_data.setdefault('ingredients', [])
            recipe_data.setdefault('instructions', [])

            # Ensure ingredients have all required fields
            for ing in recipe_data['ingredients']:
                ing.setdefault('quantity', '')
                ing.setdefault('measurement', '')
                ing.setdefault('ingredient', '')
                ing.setdefault('preparation', '')

            return recipe_data

        except json.JSONDecodeError as e:
            print(f"AI JSON Parse Error: {str(e)}")
            print(f"Raw response was: {response_text}")
            return None
        except Exception as e:
            print(f"AI Extraction Error (attempt {attempt + 1}): {str(e)}")
            if attempt < 2:
                wait_time = (attempt + 1) * 3  # 3s, then 6s
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(traceback.format_exc())
                return None