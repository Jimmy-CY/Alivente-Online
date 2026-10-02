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

THE MODEL IS NOT TYPED INTO THE CALL ANY MORE. It is MODEL, below,
which reads RECIPE_IMPORT_MODEL from the environment and falls back to
claude-sonnet-4-6 - the shape recipe_ai.py already uses for its own
RECIPE_AI_MODEL. This note used to read "Update via the model string in
extract_recipe_with_ai when migrating to a newer model", and nobody did:
the string stayed on the dated Sonnet 4 snapshot (the 14 May 2025 build)
past that model's retirement on 15 June 2026, so every import from that
day until 1 October failed with model_not_found and told the user to try
a different file.

THE EXACT DEAD ID IS NOT WRITTEN ANYWHERE IN THIS FILE, on purpose. It
is spelled out in apply_import_model.py, which is the round's record;
here it is described instead, so that a gate can assert the literal
appears nowhere in the tree and mean it.

Sonnet rather than Haiku because this module has a VISION path - a
photographed recipe is read and parsed in one call.
                                                 [test_ai_models.py]

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
import logging
import os
import time
from io import BytesIO

import anthropic
import PyPDF2
from docx import Document
from PIL import Image

from django.conf import settings

logger = logging.getLogger(__name__)

# THE ONE PLACE THE MODEL IS NAMED.
#
# It was typed twice - once in the image branch and once in the text
# branch - and both named the dated Sonnet 4 snapshot, which Anthropic
# retired on 15 June 2026. The API answered model_not_found, the retry
# loop tried three times over nine seconds, and the view said "Could not
# extract recipe data. Please try a different file." for three and a half
# months, about files that were perfectly fine.
#
# FROM THE ENVIRONMENT, so the next retirement is a Railway variable
# rather than a deploy. recipe_ai.py has read RECIPE_AI_MODEL this way
# all along; this is the same shape.          [test_ai_models.py]
MODEL = os.environ.get('RECIPE_IMPORT_MODEL', 'claude-sonnet-4-6')

# How many times the API call is retried, and the backoff between them.
# Named rather than computed inside the loop so the suite can read them
# and so the nine-second wait is visible from here.
ATTEMPTS = 3
BACKOFF = 3

# THE EXTENSION IS NOT THE MEDIA TYPE. The media type used to be built
# by interpolating the file extension into a format string, so a file
# ending in .jpg - which is what phones and scanners produce - asked the
# API for a media type spelled with that extension, and no such media
# type is registered. The right name is image/jpeg; the three-letter
# spelling is a leftover from eight-character filenames. The other two
# extensions worked only because for them the two strings coincide.
#
# Like the retired model id above, the broken spelling is DESCRIBED here
# rather than written out, so a gate can assert it appears nowhere in the
# tree and mean it. apply_import_model.py carries the literal.
#                                               [test_ai_models.py]
MEDIA_TYPES = {
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
}


class RecipeExtractionError(Exception):
    """A reason the import failed, fit to show the person who uploaded.

    THE POINT OF THIS CLASS IS THAT THE REASONS ARE DIFFERENT.
    extract_recipe_with_ai used to return None for all of them - a
    retired model, a missing key, a rate limit, a reply that was not
    JSON - and the view turned every None into one sentence blaming the
    file. The file is the one thing that is usually innocent.
    """


# ============================================
# FILE EXTRACTION FUNCTIONS
# ============================================

def extract_text_from_pdf(file):
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            # `or ''` - extract_text() returns None for a page with no
            # text layer, and `str += None` is a TypeError. [R1]
            text += page.extract_text() or ''
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

    # NOTHING TO SEND IS THE ONE CASE WHERE THE FILE IS AT FAULT.
    #
    # A scanned PDF with no text layer is the real example: PyPDF2 walks
    # its pages, finds no extractable text, and returns ''. Asking the
    # model to find a recipe in an empty string wastes three attempts and
    # nine seconds to arrive at the same answer. Said here, before the
    # call, and said as itself - this is the ONLY failure for which "try
    # a different file" is true.
    if file_type not in ('jpg', 'jpeg', 'png') and not (content or '').strip():
        raise RecipeExtractionError(
            'No text could be read out of that file. If it is a scan or a '
            'photograph saved as a PDF, there is no text layer to read - '
            'upload it as an image instead and it will be read by eye.')

    # Get API key from settings
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
    if not api_key:
        raise RecipeExtractionError(
            'The recipe reader is not configured on this server: no '
            'Anthropic API key is set.')

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

    last = None
    for attempt in range(ATTEMPTS):
        try:
            if file_type in ['jpg', 'jpeg', 'png']:
                message = client.messages.create(
                    model=MODEL,
                    max_tokens=4096,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": MEDIA_TYPES[file_type],
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
                    model=MODEL,
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
            # NOT RETRIED, AND THAT IS DELIBERATE: the call succeeded and
            # the model answered, so asking again costs money to get the
            # same shape back. The raw reply goes to the log, where it
            # can be read; it does NOT go to the screen, because it can
            # run to thousands of characters.
            logger.error('recipe import: reply was not JSON (%s); raw '
                         'reply was %r', e, response_text[:2000])
            raise RecipeExtractionError(
                'The recipe reader answered, but not in a form this page '
                'could read. Nothing is wrong with your file - please try '
                'once more.')
        except Exception as e:
            # THE REASON IS KEPT, not printed and dropped. `last` is what
            # the person is told if every attempt fails, so a retired
            # model says it is a retired model instead of arriving as
            # "try a different file" nine seconds later.
            last = e
            logger.warning('recipe import: attempt %d of %d failed on '
                           'model %s: %s', attempt + 1, ATTEMPTS, MODEL, e)
            if attempt < ATTEMPTS - 1:
                time.sleep((attempt + 1) * BACKOFF)
    logger.error('recipe import: gave up after %d attempts on model %s',
                 ATTEMPTS, MODEL, exc_info=last)
    raise RecipeExtractionError(
        'The recipe reader could not be reached (model %s). Your file is '
        'fine - this is a fault on our side. The reason was: %s'
        % (MODEL, last))