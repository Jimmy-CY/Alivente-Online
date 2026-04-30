"""
Quick smoke test for the USDA client.

Run from the project root:
    python manage.py shell < pages/test_usda_client.py

Or interactively in `python manage.py shell`:
    >>> from pages.usda_client import search_foods, get_food_details
    >>> results = search_foods("flour", page_size=5)
    >>> for r in results: print(r)
    >>> details = get_food_details(results[0]['fdc_id'])
    >>> print(details)
"""

from pages.usda_client import search_foods, get_food_details, USDAClientError

print("=" * 70)
print("USDA FoodData Central — smoke test")
print("=" * 70)

test_queries = ['flour', 'butter', 'egg', 'olive oil', 'chicken breast']

for query in test_queries:
    print(f"\n--- Searching for: '{query}' ---")
    try:
        results = search_foods(query, page_size=3)
    except USDAClientError as e:
        print(f"  ERROR: {e}")
        continue
    
    if not results:
        print("  No matches found.")
        continue
    
    for i, r in enumerate(results, 1):
        cal_str = f"{r['calories_per_100g']} kcal/100g" if r['calories_per_100g'] else "(no cal data)"
        brand = f" [{r['brand_owner']}]" if r['brand_owner'] else ""
        print(f"  {i}. [{r['data_type']}] {r['description'][:60]}{brand}")
        print(f"     fdc_id={r['fdc_id']}  {cal_str}")
    
    # Fetch full details for the first result
    print(f"\n  Full nutrition for top match (fdc_id={results[0]['fdc_id']}):")
    try:
        details = get_food_details(results[0]['fdc_id'])
        for key, value in details.items():
            if key.endswith('_per_100g'):
                print(f"    {key:25s} = {value}")
    except USDAClientError as e:
        print(f"  ERROR fetching details: {e}")

print("\n" + "=" * 70)
print("Test complete.")
print("=" * 70)