#!/usr/bin/env python3
"""
Test script to demonstrate the hierarchical scoring system with various medication scenarios
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langgraph_app import process_single_medication

def test_hierarchical_scoring_scenarios():
    """Test various medication matching scenarios to demonstrate hierarchical scoring"""
    
    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        api_key = input("Enter your OpenAI API key: ")
    
    print("🧪 HIERARCHICAL SCORING SYSTEM TEST")
    print("=" * 70)
    print("Testing different scenarios to demonstrate the 4-tier scoring:")
    print("1. Exact Name Match (ignoring non-alphabetic)")
    print("2. Strength Matching")
    print("3. Name Similarity")
    print("4. Category Similarity")
    print("=" * 70)
    
    # Test scenarios
    test_cases = [
        {
            "name": "Scenario 1: Perfect Match (Name + Strength)",
            "medication": {
                "name": "Rantac",
                "strength": "150mg",
                "form": "tablet"
            },
            "diagnoses": ["Gastritis", "GERD"],
            "expected": "Should get ~85% confidence (40 + 30 + extra)"
        },
        {
            "name": "Scenario 2: Exact Name, Different Strength", 
            "medication": {
                "name": "Rantac",
                "strength": "75mg",  # Different from available 150mg/300mg
                "form": "tablet"
            },
            "diagnoses": ["Gastritis"],
            "expected": "Should get ~75% confidence (40 + 0 strength + extra)"
        },
        {
            "name": "Scenario 3: Similar Name with Punctuation (CifranCT vs Cifran C.T.)",
            "medication": {
                "name": "CifranCT",
                "strength": "500mg",
                "form": "tablet"
            },
            "diagnoses": ["UTI", "Bacterial Infection"],
            "expected": "Should handle punctuation differences well"
        },
        {
            "name": "Scenario 4: Generic Name vs Brand",
            "medication": {
                "name": "Ranitidine",  # Generic name for Rantac
                "strength": "150mg",
                "form": "tablet"
            },
            "diagnoses": ["Gastritis"],
            "expected": "Should find Rantac as category match"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔬 {test_case['name']}")
        print("-" * 50)
        print(f"   Medication: {test_case['medication']['name']}")
        print(f"   Strength: {test_case['medication']['strength']}")
        print(f"   Expected: {test_case['expected']}")
        print()
        
        try:
            result = process_single_medication(
                medication=test_case['medication'],
                diagnoses_list=test_case['diagnoses'],
                model="gpt-5.5",
                medication_index=i-1,
                api_key=api_key
            )
            
            confidence = result.get('selection_confidence', 0)
            breakdown = result.get('hierarchical_breakdown', {})
            
            print(f"   📊 RESULTS:")
            print(f"      Final Confidence: {confidence}%")
            if breakdown:
                print(f"      Score Breakdown:")
                print(f"        • Exact Name: {breakdown.get('exact_name', 0)}/40 points")
                print(f"        • Strength: {breakdown.get('strength', 0)}/30 points")
                print(f"        • Name Similarity: {breakdown.get('name_similarity', 0)}/20 points")
                print(f"        • Category: {breakdown.get('category', 0)}/10 points")
                print(f"        • Total: {breakdown.get('total', 0)}/100 points")
            
            print(f"      Selected Product: {result.get('pharmeasy_name', 'Not found')}")
            print(f"      URL: {result.get('url', 'No URL')}")
            
            # Confidence assessment
            if confidence >= 80:
                print(f"      ✅ HIGH CONFIDENCE - Excellent match!")
            elif confidence >= 60:
                print(f"      ⚠️  MEDIUM CONFIDENCE - Good match")
            else:
                print(f"      ❌ LOW CONFIDENCE - May need review")
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    print(f"\n" + "=" * 70)
    print("🎯 HIERARCHICAL SCORING SUMMARY:")
    print("• Exact Name Match: 40 points (most important)")
    print("• Strength Match: 30 points (second priority)")  
    print("• Name Similarity: 20 points (third priority)")
    print("• Category Similarity: 10 points (fourth priority)")
    print("• Total possible: 100 points = 100% confidence")
    print("• Minimum boost: 75% for strong exact name matches")
    print("=" * 70)

if __name__ == "__main__":
    test_hierarchical_scoring_scenarios()
