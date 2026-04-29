#!/usr/bin/env python3
"""
Test script to check Rantac medication matching with improved confidence scoring
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path to import langgraph_app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langgraph_app import process_single_medication, fetch_pharmeasy_content, parse_pharmeasy_products, select_best_product_match

def test_rantac_matching():
    """Test Rantac medication matching"""
    
    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        api_key = input("Enter your OpenAI API key: ")
    
    print("🧪 Testing Rantac Medication Matching")
    print("=" * 50)
    
    # Test medication data
    test_medication = {
        "name": "Rantac",
        "strength": "150mg",
        "form": "tablet",
        "instructions": "twice daily after meals"
    }
    
    # Test diagnoses (common conditions Rantac is used for)
    test_diagnoses = ["Gastritis", "Acid Reflux", "GERD"]
    
    print(f"🔍 Testing medication: {test_medication['name']}")
    print(f"   Strength: {test_medication['strength']}")
    print(f"   Form: {test_medication['form']}")
    print(f"   Instructions: {test_medication['instructions']}")
    print(f"   Diagnoses: {', '.join(test_diagnoses)}")
    print()
    
    try:
        # Test the full medication processing pipeline
        result = process_single_medication(
            medication=test_medication,
            diagnoses_list=test_diagnoses,
            model="gpt-5.4",
            medication_index=0,
            api_key=api_key
        )
        
        print("📊 RESULTS:")
        print("=" * 30)
        print(f"✅ Medication processed successfully!")
        print(f"🎯 Final URL: {result.get('url', 'No URL')}")
        print(f"🏷️  PharmeEasy Name: {result.get('pharmeasy_name', 'Not found')}")
        print(f"📈 Confidence: {result.get('selection_confidence', 0)}%")
        print(f"🧠 Reasoning: {result.get('selection_reasoning', 'No reasoning')}")
        print(f"🔗 Name Similarity: {result.get('name_similarity', 'unknown')}")
        print(f"💊 Strength Match: {result.get('strength_match', 'unknown')}")
        print(f"📋 Form Match: {result.get('form_match', 'unknown')}")
        
        # Check if name was modified
        if result.get('modified_name'):
            print(f"⚠️  Name Modified: {test_medication['name']} → {result.get('modified_name')}")
            print(f"📝 Reason: {result.get('reason', 'No reason provided')}")
        
        # Show alternative products if available
        all_products = result.get('all_products', [])
        if all_products:
            print(f"\n🛒 Found {len(all_products)} total products:")
            for i, product in enumerate(all_products[:5]):  # Show first 5
                print(f"   {i+1}. {product.get('name', 'Unknown')} - {product.get('url', 'No URL')}")
            if len(all_products) > 5:
                print(f"   ... and {len(all_products) - 5} more")
        
        print(f"\n🎯 SUCCESS: Confidence score is {result.get('selection_confidence', 0)}%")
        if result.get('selection_confidence', 0) >= 75:
            print("✅ HIGH CONFIDENCE - Exact match likely found!")
        elif result.get('selection_confidence', 0) >= 50:
            print("⚠️  MEDIUM CONFIDENCE - Good match found")
        else:
            print("❌ LOW CONFIDENCE - May need manual review")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def test_detailed_matching():
    """Test the detailed matching steps for Rantac"""
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        api_key = input("Enter your OpenAI API key: ")
    
    print("\n🔬 DETAILED MATCHING TEST")
    print("=" * 50)
    
    # Step 1: Fetch content
    print("📥 Step 1: Fetching PharmeEasy content for 'Rantac'...")
    html_content = fetch_pharmeasy_content("Rantac")
    
    if html_content:
        print(f"✅ Content fetched successfully ({len(html_content)} characters)")
        
        # Step 2: Parse products
        print("🔍 Step 2: Parsing products from HTML...")
        products = parse_pharmeasy_products(html_content, "gpt-5.4", api_key=api_key)
        
        if products:
            print(f"✅ Found {len(products)} products:")
            for i, product in enumerate(products[:5]):
                print(f"   {i}. {product.get('name', 'Unknown')}")
            
            # Step 3: Test LLM selection
            print("\n🧠 Step 3: Testing LLM product selection...")
            selection_result = select_best_product_match(
                medicine_name="Rantac",
                products=products,
                diagnoses=["Gastritis", "Acid Reflux"],
                model="gpt-5.4",
                medication_details={"name": "Rantac", "strength": "150mg", "form": "tablet"},
                api_key=api_key
            )
            
            if selection_result["success"]:
                analysis = selection_result["analysis"]
                selected_product = selection_result["product"]
                
                print("✅ LLM Analysis Results:")
                print(f"   Selected: {selected_product.get('name', 'Unknown')}")
                print(f"   Confidence: {analysis.get('confidence_score', 0)}%")
                print(f"   Name Similarity: {analysis.get('name_similarity', 'unknown')}")
                print(f"   Strength Match: {analysis.get('strength_match', 'unknown')}")
                print(f"   Form Match: {analysis.get('form_match', 'unknown')}")
                print(f"   Reasoning: {analysis.get('reasoning', 'No reasoning')}")
            else:
                print("❌ LLM selection failed")
                print(f"   Analysis: {selection_result.get('analysis', {})}")
        else:
            print("❌ No products found in HTML content")
    else:
        print("❌ Failed to fetch content from PharmeEasy")

if __name__ == "__main__":
    print("🧪 RANTAC MEDICATION MATCHING TEST")
    print("=" * 60)
    
    # Test basic matching
    test_rantac_matching()
    
    # Test detailed steps
    test_detailed_matching()
    
    print("\n✅ Test completed!")
