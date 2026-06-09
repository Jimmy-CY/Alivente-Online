# audit_mojibake.py
# Self-discovering mojibake audit across Recipe + all related models.
from pages.models import Recipe, RecipeIngredient, Ingredient
from django.db.models import CharField, TextField
import re

SIG = r'[ÂâÃ]'

def audit_model(model):
    text_fields = [f.name for f in model._meta.fields
                   if isinstance(f, (CharField, TextField))]
    if not text_fields:
        return
    pk_name = model._meta.pk.name
    header_printed = False
    for field in text_fields:
        try:
            qs = model.objects.filter(**{f'{field}__regex': SIG})
            count = qs.count()
        except Exception as e:
            continue
        if count == 0:
            continue
        if not header_printed:
            print(f'\n=== {model.__name__} ({model.objects.count()} total rows) ===')
            header_printed = True
        print(f'  {field}: {count} affected')
        for r in qs[:5]:
            val = getattr(r, field) or ''
            preview = (val[:80] + '…') if len(val) > 80 else val
            print(f'    {pk_name}={getattr(r, pk_name)}: {preview!r}')

# Walk Recipe + RecipeIngredient + Ingredient and all reverse-FK related models
seen = set()
def visit(model):
    if model in seen:
        return
    seen.add(model)
    audit_model(model)
    for rel in model._meta.related_objects:
        visit(rel.related_model)

for m in [Recipe, RecipeIngredient, Ingredient]:
    visit(m)

print(f'\n=== Models inspected ({len(seen)}) ===')
for m in sorted(seen, key=lambda x: x.__name__):
    text_fields = [f.name for f in m._meta.fields
                   if isinstance(f, (CharField, TextField))]
    print(f'  {m.__name__}: {text_fields}')