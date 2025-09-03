#!/usr/bin/env python3
"""
Debug the category matching logic
"""

def debug_category_matching():
    """Debug why category matching is showing 0 points"""
    
    print("🔍 DEBUGGING CATEGORY MATCHING")
    print("=" * 50)
    
    # Test case 1: Rantac tablet
    medicine_name = "Rantac"
    product_name = "Rantac 150mg Strip Of 30 Tablets"
    
    print(f"Test 1: '{medicine_name}' vs '{product_name}'")
    
    medicine_lower = medicine_name.lower()
    product_lower = product_name.lower()
    
    print(f"  Medicine (lower): '{medicine_lower}'")
    print(f"  Product (lower): '{product_lower}'")
    
    # Categories and forms
    categories = ['tablet', 'syrup', 'capsule', 'injection', 'cream', 'ointment', 'drops']
    forms = ['strip', 'bottle', 'vial', 'tube']
    
    medicine_categories = [cat for cat in categories if cat in medicine_lower]
    product_categories = [cat for cat in categories if cat in product_lower]
    
    medicine_forms = [form for form in forms if form in medicine_lower]
    product_forms = [form for form in forms if form in product_lower]
    
    print(f"  Medicine categories found: {medicine_categories}")
    print(f"  Product categories found: {product_categories}")
    print(f"  Medicine forms found: {medicine_forms}")
    print(f"  Product forms found: {product_forms}")
    
    category_score = 0
    if set(medicine_categories).intersection(set(product_categories)):
        category_score += 5
        print(f"  ✅ Category match: +5 points")
    else:
        print(f"  ❌ No category match")
    
    if set(medicine_forms).intersection(set(product_forms)):
        category_score += 5
        print(f"  ✅ Form match: +5 points")
    else:
        print(f"  ❌ No form match")
    
    print(f"  Total category score: {category_score}/10")
    
    print(f"\n" + "="*30)
    
    # Test case 2: With medication details that include form
    print(f"Test 2: Using medication details with form='tablet'")
    
    # Simulate what should happen when we have medication details
    medication_form = "tablet"
    combined_medicine_text = f"{medicine_name} {medication_form}"
    medicine_lower_with_form = combined_medicine_text.lower()
    
    print(f"  Combined medicine text: '{combined_medicine_text}'")
    print(f"  Medicine (lower with form): '{medicine_lower_with_form}'")
    
    medicine_categories_with_form = [cat for cat in categories if cat in medicine_lower_with_form]
    print(f"  Medicine categories with form: {medicine_categories_with_form}")
    
    category_score_corrected = 0
    if set(medicine_categories_with_form).intersection(set(product_categories)):
        category_score_corrected += 5
        print(f"  ✅ Category match with form: +5 points")
    
    if set(medicine_forms).intersection(set(product_forms)):
        category_score_corrected += 5
        print(f"  ✅ Form match: +5 points")
    
    print(f"  Corrected category score: {category_score_corrected}/10")
    
    print(f"\n🎯 ISSUE IDENTIFIED:")
    print(f"The problem is that we're only checking the medicine NAME for categories,")
    print(f"but we should also check the medication details (form, instructions, etc.)")
    print(f"")
    print(f"Current logic: Only looks in 'Rantac' for 'tablet' ❌")  
    print(f"Should be: Look in 'Rantac tablet' or medication_details ✅")

if __name__ == "__main__":
    debug_category_matching()
