#!/usr/bin/env python3
"""
Simple test to demonstrate exact name matching with punctuation differences
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langgraph_app import select_best_product_match

def test_exact_name_matching():
    """Test the exact name matching logic with punctuation variations"""
    
    print("🧪 EXACT NAME MATCHING TEST")
    print("=" * 50)
    
    # Mock products that simulate punctuation differences
    mock_products = [
        {"name": "Cifran C.T. 500mg Strip Of 10 Tablets", "url": "https://example.com/1"},
        {"name": "Cifran CT 250mg Strip Of 6 Tablets", "url": "https://example.com/2"},  
        {"name": "CifranCT 500mg Strip Of 10 Tablets", "url": "https://example.com/3"},
        {"name": "Amoxicillin 500mg Capsules", "url": "https://example.com/4"},
        {"name": "Cifran-CT 500mg Tablets", "url": "https://example.com/5"}
    ]
    
    # Test medication details
    medication_details = {
        "name": "CifranCT",
        "strength": "500mg", 
        "form": "tablet"
    }
    
    print(f"🔍 Testing medication: {medication_details['name']}")
    print(f"   Strength: {medication_details['strength']}")
    print(f"   Available products:")
    for i, product in enumerate(mock_products):
        print(f"      {i}. {product['name']}")
    
    print("\n📊 HIERARCHICAL SCORING RESULTS:")
    print("-" * 40)
    
    # Test the selection
    result = select_best_product_match(
        medicine_name="CifranCT",
        products=mock_products,
        diagnoses=["UTI", "Bacterial Infection"],
        medication_details=medication_details
    )
    
    if result["success"]:
        analysis = result["analysis"]
        selected_product = result["product"]
        breakdown = analysis.get("hierarchical_breakdown", {})
        
        print(f"✅ Selected: {selected_product['name']}")
        print(f"📈 Confidence: {analysis['confidence_score']}%")
        print(f"🔍 Score Breakdown:")
        print(f"   • Exact Name: {breakdown.get('exact_name', 0)}/40 points")
        print(f"   • Strength: {breakdown.get('strength', 0)}/30 points") 
        print(f"   • Name Similarity: {breakdown.get('name_similarity', 0)}/20 points")
        print(f"   • Category: {breakdown.get('category', 0)}/10 points")
        print(f"   • Total: {breakdown.get('total', 0)}/100 points")
        print(f"📝 Reasoning: {analysis['reasoning']}")
        
        print(f"\n🎯 EXACT NAME MATCHING ANALYSIS:")
        print("   The system should recognize that:")
        print("   • 'CifranCT' matches 'Cifran C.T.' (ignoring punctuation)")
        print("   • 'CifranCT' matches 'Cifran CT' (ignoring spaces)")
        print("   • 'CifranCT' matches 'CifranCT' (exact match)")
        print("   • 'CifranCT' matches 'Cifran-CT' (ignoring hyphens)")
        
        # Check which products would be considered exact matches
        def normalize_name_for_exact_match(text: str) -> str:
            """Normalize text by removing non-alphabetic characters and converting to lowercase."""
            import re
            return re.sub(r'[^a-zA-Z]', '', text).lower()
        
        print(f"\n🔍 DETAILED MATCHING ANALYSIS:")
        medicine_normalized = normalize_name_for_exact_match("CifranCT")
        print(f"   Normalized search term: '{medicine_normalized}'")
        
        for i, product in enumerate(mock_products):
            product_normalized = normalize_name_for_exact_match(product['name'])
            is_match = medicine_normalized in product_normalized or product_normalized in medicine_normalized
            match_symbol = "✅" if is_match else "❌"
            print(f"   {match_symbol} Product {i}: '{product_normalized}' - {is_match}")
            
    else:
        print("❌ Selection failed")

if __name__ == "__main__":
    test_exact_name_matching()
