#!/usr/bin/env python3
"""
Debug script to check what's in the PharmeEasy HTML for Rantac
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langgraph_app import fetch_pharmeasy_content, parse_pharmeasy_products

def debug_pharmeasy_content():
    """Debug what's actually in the PharmeEasy content"""
    
    print("🔍 DEBUGGING PHARMEASY CONTENT FOR RANTAC")
    print("=" * 60)
    
    # Fetch content
    print("📥 Fetching content...")
    html_content = fetch_pharmeasy_content("Rantac")
    
    if html_content:
        print(f"✅ Content fetched: {len(html_content)} characters")
        
        # Save to file for inspection
        with open('rantac_debug.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("💾 Saved full HTML to 'rantac_debug.html'")
        
        # Check for common product indicators
        indicators = [
            'product',
            'medicine',
            'drug',
            'rantac',
            'tablet',
            'pharmeasy',
            'price',
            'buy',
            'cart',
            'mg',
            'ranitidine'
        ]
        
        print("\n🔍 Checking for key indicators:")
        for indicator in indicators:
            count = html_content.lower().count(indicator.lower())
            print(f"   '{indicator}': {count} occurrences")
        
        # Look for specific patterns
        print("\n🔍 Looking for URL patterns:")
        import re
        
        # Look for href patterns
        hrefs = re.findall(r'href=["\']([^"\']*)["\']', html_content)
        product_hrefs = [href for href in hrefs if 'product' in href.lower() or 'medicine' in href.lower()]
        print(f"   Found {len(hrefs)} total hrefs")
        print(f"   Found {len(product_hrefs)} product-related hrefs")
        
        if product_hrefs:
            print("   Sample product hrefs:")
            for href in product_hrefs[:5]:
                print(f"     {href}")
        
        # Look for product names
        print("\n🔍 Looking for potential product names:")
        # Common patterns for product names
        patterns = [
            r'Rantac[^<>]*(?:150|mg|tablet)',
            r'Ranitidine[^<>]*(?:150|mg|tablet)',
            r'title=["\']([^"\']*[Rr]antac[^"\']*)["\']',
            r'alt=["\']([^"\']*[Rr]antac[^"\']*)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                print(f"   Pattern '{pattern}': {len(matches)} matches")
                for match in matches[:3]:
                    print(f"     {match}")
        
        # Show first 2000 characters to see page structure
        print("\n📄 First 2000 characters of content:")
        print("-" * 50)
        print(html_content[:2000])
        print("-" * 50)
        
        # Show last 1000 characters 
        print("\n📄 Last 1000 characters of content:")
        print("-" * 50)
        print(html_content[-1000:])
        print("-" * 50)
        
    else:
        print("❌ Failed to fetch content")

if __name__ == "__main__":
    debug_pharmeasy_content()
