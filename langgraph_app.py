from langgraph.graph import StateGraph
from typing import TypedDict, List, Dict, Any
import openai
import base64
import os
import json
import requests
from urllib.parse import quote
import re

# Define the state structure
class GraphState(TypedDict):
    images: List[str]
    markdown: str
    diagnoses: Dict[str, Any]
    medications: Dict[str, Any]
    fixed_medications: Dict[str, Any]
    html_summary: str

def get_openai_params(model: str, messages: list, max_tokens: int = 2048, temperature: float = 0.1, use_json_format: bool = True) -> dict:
    """
    Get the correct OpenAI API parameters based on the model type.
    """
    base_params = {
        "model": model,
        "messages": messages
    }
    
    # Handle different model families
    if model.startswith("gpt-5") or model.startswith("o1") or model.startswith("o3"):
        # For GPT-5, o1, and o3 models, use max_completion_tokens
        base_params["max_completion_tokens"] = max_tokens
        
        # o1 and o3 models don't support response_format, temperature
        if model.startswith("o1") or model.startswith("o3"):
            pass  # No additional params for o1/o3
        elif model.startswith("gpt-5"):
            # GPT-5 models: only support temperature=1 (default)
            base_params["temperature"] = 1
            if use_json_format:
                base_params["response_format"] = {"type": "json_object"}
    else:
        # For GPT-4 and older models, use max_tokens
        base_params["max_tokens"] = max_tokens
        base_params["temperature"] = temperature
        if use_json_format:
            base_params["response_format"] = {"type": "json_object"}
    
    return base_params

def ocr_node(state: GraphState, model: str = "gpt-4o-mini") -> GraphState:
    """
    Process images and extract text using GPT-4 Vision.
    """
    system_prompt = """Task. You are an expert medical assistant working in a hospital located 
    in Kolkata, India. Transcribe this discharge summary issued to a patient exactly 
    (i.e. preserve all sections/headers/order/wording). If in doubt about some unclear writing,
      try to match with terms that make sense in an India context, for medical field and 
      relevant diagnoses, and check medications against India availability. Then output a 
      simple markdown document with all the contents with the same content as the original"""
    
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Process images
    image_contents = []
    for image_path in state.get("images", []):
        try:
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
                
            image_type = "image/jpeg" if image_path.lower().endswith(('.jpg', '.jpeg')) else "image/png"
            
            image_contents.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image_type};base64,{image_data}"
                }
            })
        except FileNotFoundError:
            print(f"Warning: Image file not found: {image_path}")
            continue
    
    if not image_contents:
        markdown_text = "# OCR Error\nNo valid images found to process."
    else:
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Please transcribe these medical discharge summary pages into markdown format."}
                    ] + image_contents
                }
            ]
            
            api_params = get_openai_params(model, messages, max_tokens=4096, use_json_format=False)
            response = client.chat.completions.create(**api_params)
            markdown_text = response.choices[0].message.content
            
        except Exception as e:
            print(f"Error processing images with OpenAI API: {e}")
            markdown_text = f"# OCR Error\nFailed to process images: {str(e)}"
    
    # Print the markdown text
    print(f"=== OCR Node Output (Model: {model}) ===")
    print(markdown_text)
    print("======================")
    
    state["markdown"] = markdown_text
    return state

def extract_diagnoses_node(state: GraphState, model: str = "gpt-4o-mini") -> GraphState:
    """
    Extract diagnoses and lab tests from the markdown text.
    """
    markdown_text = state.get("markdown", "")
    
    system_prompt = """You are an expert medical doctor practising in Kolkata India. You have been given a hospital discharge report of a patient in simple mardown text format. Your job is to identify all the relevant medical terms in the document related to a) diagnosis names b) lab test names from the document. Ignore all medicine names. Keep in mind common terminology used in that part of the world. Return a JSON structure of the form
{"diagnoses": ["diagnosis term 1", "diagnosis term 2", ...], "lab_tests":["lab test name 1", "lab test name 2", ...]}"""
    
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please extract diagnoses and lab tests from this discharge summary:\n\n{markdown_text}"}
        ]
        
        api_params = get_openai_params(model, messages, max_tokens=2048, use_json_format=True)
        response = client.chat.completions.create(**api_params)
        diagnoses_json = json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"Error extracting diagnoses with OpenAI API: {e}")
        diagnoses_json = {"diagnoses": [], "lab_tests": []}
    
    # Print the diagnoses output
    print(f"=== Extract Diagnoses Node Output (Model: {model}) ===")
    print(diagnoses_json)
    print("====================================")
    
    state["diagnoses"] = diagnoses_json
    return state

def extract_medications_node(state: GraphState, model: str = "gpt-4o-mini") -> GraphState:
    """
    Extract medications from the markdown text.
    """
    markdown_text = state.get("markdown", "")
    
    system_prompt = """You are an expert medical doctor practising in Kolkata India. You have been given a hospital discharge report of a patient in simple mardown text format. Your job is to identify all the relevant medication names from the document along with instructions. In case of difficulty identifying a medication name, make sure the names match actual medications used in that part of the world. Return a JSON structure of the form
{"medications": [{"name":"medicine_1", "instructions":"Twice daily", "duration":"continue"}, {"name":"medicine_2", "instructions":"as needed", "duration":"as needed"}, {"name":"medicine_3", "instructions":"BID", "duration":"10 days"}]}"""
    
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please extract medications with instructions and duration from this discharge summary:\n\n{markdown_text}"}
        ]
        
        api_params = get_openai_params(model, messages, max_tokens=2048, use_json_format=True)
        response = client.chat.completions.create(**api_params)
        medications_json = json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"Error extracting medications with OpenAI API: {e}")
        medications_json = {"medications": []}
    
    # Print the medications output
    print(f"=== Extract Medications Node Output (Model: {model}) ===")
    print(medications_json)
    print("======================================================")
    
    state["medications"] = medications_json
    return state

def fetch_pharmeasy_content(medicine_name: str) -> str:
    """
    Fetch the HTML content from PharmeEasy search page.
    """
    try:
        encoded_medicine = quote(medicine_name)
        search_url = f"https://pharmeasy.in/search/all?name={encoded_medicine}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        print(f"Fetching: {search_url}")
        
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(search_url, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        content = response.text
        print(f"Fetched {len(content)} characters from PharmeEasy")
        
        return content
        
    except Exception as e:
        print(f"Error fetching Pharmeasy content: {e}")
        return ""

def parse_pharmeasy_products(html_content: str, model: str = "gpt-4o-mini") -> List[Dict[str, str]]:
    """
    Use LLM to parse PharmeEasy HTML and extract product listings.
    """
    try:
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        system_prompt = """You are an expert web scraper. Parse this HTML content from Pharmeasy.in search results.

Look for product listings in the main body of the page and extract up to 10 products. For each product, extract:
- name: The product name/title
- url: The product URL (if relative path, prepend "https://pharmeasy.in")

Look for patterns like:
- Product cards or containers
- Links to product pages (often containing "/online-medicine-order/" or "/medicines/")
- Product names in headings, spans, or divs
- Medicine names and dosages

Return JSON format:
{"products": [{"name": "Product Name 1", "url": "https://pharmeasy.in/online-medicine-order/..."}, {"name": "Product Name 2", "url": "https://pharmeasy.in/..."}, ...]}

If no products found, return empty products array."""
        
        # Truncate content to manageable size
        max_length = 15000
        if len(html_content) > max_length:
            # Keep beginning and middle sections which likely contain products
            start_chunk = html_content[:5000]
            middle_start = len(html_content) // 3
            middle_chunk = html_content[middle_start:middle_start + 10000]
            html_content = start_chunk + "\n... [content truncated] ...\n" + middle_chunk
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Parse this PharmeEasy HTML and extract product listings:\n\n{html_content}"}
        ]
        
        api_params = get_openai_params(model, messages, max_tokens=2048, use_json_format=True)
        response = client.chat.completions.create(**api_params)
        
        result = json.loads(response.choices[0].message.content)
        products = result.get("products", [])
        
        # Clean up URLs
        cleaned_products = []
        for product in products:
            url = product.get("url", "")
            if url.startswith("/"):
                url = "https://pharmeasy.in" + url
            elif not url.startswith("http") and url:
                url = "https://pharmeasy.in/" + url
            
            if product.get("name") and url:
                cleaned_products.append({
                    "name": product["name"],
                    "url": url
                })
        
        print(f"Extracted {len(cleaned_products)} products from PharmeEasy page")
        return cleaned_products
        
    except Exception as e:
        print(f"Error parsing PharmeEasy HTML: {e}")
        return []

def add_medication_pills_to_html(html_content: str, fixed_medications: Dict[str, Any], model: str = "gpt-4o-mini") -> str:
    """
    Add visual pills next to medications in the HTML content.
    """
    medications = fixed_medications.get("medications", [])
    
    for medication in medications:
        original_name = medication.get("name", "")
        pharmeasy_name = medication.get("pharmeasy_name", "")
        url = medication.get("url", "")
        confidence = medication.get("selection_confidence", 0)
        modified_name = medication.get("modified_name", "")
        
        if not original_name:
            continue
        
        # Get URL summary for hover
        url_summary = fetch_url_summary(url, model) if url else "No URL available"
        
        # Check if name was modified - use multiple criteria
        name_modified = False
        display_names = original_name
        
        if pharmeasy_name and pharmeasy_name != "Not found":
            # Check if it's actually a different product
            original_lower = original_name.lower().strip()
            pharmeasy_lower = pharmeasy_name.lower().strip()
            
            # More sophisticated name comparison
            # Consider it the same if one is contained in the other or very similar
            is_subset = (original_lower in pharmeasy_lower or pharmeasy_lower in original_lower)
            
            # Calculate simple similarity (Levenshtein-like)
            def simple_similarity(s1, s2):
                if not s1 or not s2:
                    return 0
                longer = s1 if len(s1) > len(s2) else s2
                shorter = s2 if len(s1) > len(s2) else s1
                if len(longer) == 0:
                    return 1.0
                # Count matching characters in order
                matches = 0
                for i, char in enumerate(shorter):
                    if i < len(longer) and char.lower() == longer[i].lower():
                        matches += 1
                return matches / len(longer)
            
            similarity = simple_similarity(original_lower, pharmeasy_lower)
            
            # Consider it modified if similarity is low AND not a subset match
            if similarity < 0.7 and not is_subset:
                name_modified = True
                # Show both names
                display_names = f"{original_name} → {pharmeasy_name}"
            elif modified_name and modified_name != original_name:
                # Fallback to modified_name field
                name_modified = True
                display_names = f"{original_name} → {modified_name}"
        
        warning_icon = " ⚠️" if name_modified else ""
        
        # Create pill HTML
        pill_class = "medication-pill-modified" if name_modified else "medication-pill"
        confidence_indicator = f" ({confidence}%)" if confidence > 0 else ""
        
        pill_html = f'''<span class="{pill_class}" title="{url_summary}">
            <a href="{url}" target="_blank" style="text-decoration: none; color: inherit;">
                💊 {display_names}{warning_icon}
            </a>
        </span>{confidence_indicator}'''
        
        # Find and replace medication name in HTML - try multiple approaches
        replacements_made = 0
        
        # Method 1: Exact word boundary match
        pattern1 = r'\b' + re.escape(original_name) + r'\b'
        if re.search(pattern1, html_content, re.IGNORECASE):
            html_content = re.sub(pattern1, f'{original_name} {pill_html}', html_content, count=1, flags=re.IGNORECASE)
            replacements_made += 1
        
        # Method 2: If no exact match, try case-insensitive partial match
        elif replacements_made == 0:
            # Look for the name in various forms
            search_variants = [
                original_name,
                original_name.lower(),
                original_name.upper(),
                original_name.title(),
            ]
            
            for variant in search_variants:
                if variant in html_content:
                    # Find the first occurrence and replace it
                    pos = html_content.find(variant)
                    if pos != -1:
                        html_content = html_content[:pos] + variant + ' ' + pill_html + html_content[pos + len(variant):]
                        replacements_made += 1
                        break
        
        # Method 3: If still no match, try to find partial matches
        if replacements_made == 0:
            # Split the medicine name and try to find the main component
            name_parts = original_name.split()
            for part in name_parts:
                if len(part) > 3:  # Only try meaningful parts
                    pattern = r'\b' + re.escape(part) + r'\b'
                    if re.search(pattern, html_content, re.IGNORECASE):
                        html_content = re.sub(pattern, f'{part} {pill_html}', html_content, count=1, flags=re.IGNORECASE)
                        replacements_made += 1
                        break
        
        # Debug output
        if replacements_made == 0:
            print(f"⚠️ Warning: Could not find medication '{original_name}' in HTML content")
        else:
            print(f"✓ Added pill for: {original_name} ({'modified' if name_modified else 'exact'})")
    
    return html_content

def select_best_product_match(medicine_name: str, products: List[Dict[str, str]], diagnoses: List[str], model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Use LLM to select the best matching product based on medicine name similarity, 
    diagnoses relevance, drug category, strength, etc.
    """
    try:
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        system_prompt = """You are an expert pharmacist practicing in India. Your job is to select the best matching medication product from a list of options.

Consider these factors when selecting the best match:
1. NAME SIMILARITY: How closely does the product name match the original medicine name?
   - "high": Exact match or very close (>90% similar)
   - "medium": Recognizably similar (70-90% similar) 
   - "low": Different but same category (<70% similar)
2. DRUG CATEGORY: Does the medication category match what would be expected for the diagnoses?
3. STRENGTH/DOSAGE: Is the strength appropriate and commonly prescribed?
4. FORMULATION: Is the formulation (tablet, syrup, injection, etc.) appropriate?
5. BRAND VS GENERIC: Consider both brand and generic equivalents
6. COMMON USAGE: Is this a commonly prescribed medication for the given diagnoses?

IMPORTANT: When evaluating name similarity, consider:
- Exact matches or minor variations (like "Paracetamol" vs "Paracetamol 500mg") should be "high"
- Same drug different brand (like "Paracetamol" vs "Crocin") should be "medium" 
- Single character differences should be "high" similarity
- Generic vs brand names of same drug should be "medium" to "high"

Return your analysis in JSON format:
{
  "selected_product_index": 0,
  "confidence_score": 85,
  "reasoning": "Detailed explanation of why this product was selected",
  "name_similarity": "high/medium/low",
  "dosage_appropriateness": "appropriate/too_high/too_low/unknown",
  "category_match": "exact/similar/different",
  "alternative_suggestions": [1, 2]
}

If no good match is found, set selected_product_index to -1."""
        
        # Prepare the product list for analysis
        products_text = ""
        for i, product in enumerate(products):
            products_text += f"{i}. {product['name']} - {product['url']}\n"
        
        diagnoses_text = ", ".join(diagnoses) if diagnoses else "No specific diagnoses provided"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""Please analyze and select the best matching product:

Original medicine name: {medicine_name}
Patient diagnoses: {diagnoses_text}

Available products:
{products_text}

Select the best match considering name similarity, appropriateness for the diagnoses, dosage strength, and common medical practice in India. Pay special attention to accurate name similarity scoring."""}
        ]
        
        api_params = get_openai_params(model, messages, max_tokens=1024, use_json_format=True)
        response = client.chat.completions.create(**api_params)
        
        result = json.loads(response.choices[0].message.content)
        
        selected_index = result.get("selected_product_index", -1)
        
        if selected_index >= 0 and selected_index < len(products):
            return {
                "product": products[selected_index],
                "analysis": result,
                "success": True
            }
        else:
            return {
                "product": None,
                "analysis": result,
                "success": False
            }
            
    except Exception as e:
        print(f"Error in product selection: {e}")
        return {
            "product": products[0] if products else None,
            "analysis": {"reasoning": f"Error in selection, using first product: {str(e)}", "name_similarity": "unknown"},
            "success": False
        }

def fix_medications_node(state: GraphState, model: str = "gpt-4o-mini") -> GraphState:
    """
    Fetch PharmeEasy content for each medication and use LLM to select the best matching product.
    """
    medications_data = state.get("medications", {"medications": []})
    diagnoses_data = state.get("diagnoses", {"diagnoses": [], "lab_tests": []})
    diagnoses_list = diagnoses_data.get("diagnoses", [])
    
    fixed_medications_list = []
    
    for i, medication in enumerate(medications_data.get("medications", [])):
        medicine_name = medication.get('name', 'Unknown')
        print(f"\n--- Processing medication {i+1}: {medicine_name} ---")
        
        try:
            # Fetch Pharmeasy page content
            html_content = fetch_pharmeasy_content(medicine_name)
            
            if html_content:
                # Parse products from the HTML
                products = parse_pharmeasy_products(html_content, model)
                
                # Create enhanced medication object
                medication_copy = medication.copy()
                
                if products:
                    print(f"Found {len(products)} products, selecting best match...")
                    
                    # Use LLM to select the best matching product
                    selection_result = select_best_product_match(
                        medicine_name, 
                        products, 
                        diagnoses_list, 
                        model
                    )
                    
                    if selection_result["success"] and selection_result["product"]:
                        primary_product = selection_result["product"]
                        analysis = selection_result["analysis"]
                        
                        medication_copy.update({
                            "url": primary_product["url"],
                            "pharmeasy_name": primary_product["name"],
                            "all_products": products[:10],  # Store up to 10 products
                            "selection_confidence": analysis.get("confidence_score", 0),
                            "selection_reasoning": analysis.get("reasoning", ""),
                            "name_similarity": analysis.get("name_similarity", "unknown"),
                            "dosage_appropriateness": analysis.get("dosage_appropriateness", "unknown"),
                            "category_match": analysis.get("category_match", "unknown")
                        })
                        
                        # Check if name differs significantly
                        original_lower = medicine_name.lower()
                        pharmeasy_lower = primary_product["name"].lower()
                        
                        if original_lower not in pharmeasy_lower and pharmeasy_lower not in original_lower:
                            medication_copy["modified_name"] = primary_product["name"]
                            medication_copy["reason"] = f"LLM selected best match: {primary_product['name']} (confidence: {analysis.get('confidence_score', 0)}%)"
                        
                        print(f"✓ LLM selected: {primary_product['name']}")
                        print(f"  Confidence: {analysis.get('confidence_score', 0)}%")
                        print(f"  Reasoning: {analysis.get('reasoning', 'No reasoning provided')[:100]}...")
                        
                        # Show alternative suggestions if available
                        alternatives = analysis.get("alternative_suggestions", [])
                        if alternatives:
                            alt_names = []
                            for alt_idx in alternatives:
                                if isinstance(alt_idx, int) and 0 <= alt_idx < len(products):
                                    alt_names.append(products[alt_idx]["name"])
                            if alt_names:
                                print(f"  Alternatives: {', '.join(alt_names[:2])}")
                    
                    else:
                        # LLM couldn't find a good match, use first product as fallback
                        primary_product = products[0]
                        analysis = selection_result["analysis"]
                        
                        medication_copy.update({
                            "url": primary_product["url"],
                            "pharmeasy_name": primary_product["name"],
                            "all_products": products[:10],
                            "selection_confidence": 0,
                            "selection_reasoning": analysis.get("reasoning", "No good match found, using first result"),
                            "modified_name": primary_product["name"],
                            "reason": f"No good match found (LLM analysis), using: {primary_product['name']}"
                        })
                        
                        print(f"⚠ LLM found no good match, using first result: {primary_product['name']}")
                        print(f"  Reasoning: {analysis.get('reasoning', 'No reasoning provided')}")
                
                else:
                    # No products found in parsed content
                    fallback_url = f"https://pharmeasy.in/search/all?name={medicine_name.replace(' ', '%20')}"
                    medication_copy.update({
                        "url": fallback_url,
                        "reason": "No products found in page content, using search URL",
                        "all_products": [],
                        "selection_confidence": 0
                    })
                    print(f"✗ No products extracted from page content")
            else:
                # Failed to fetch content
                fallback_url = f"https://pharmeasy.in/search/all?name={medicine_name.replace(' ', '%20')}"
                medication_copy = medication.copy()
                medication_copy.update({
                    "url": fallback_url,
                    "reason": "Failed to fetch page content, using search URL",
                    "all_products": [],
                    "selection_confidence": 0
                })
                print(f"✗ Failed to fetch page content")
            
            fixed_medications_list.append(medication_copy)
            
        except Exception as e:
            print(f"✗ Error processing {medicine_name}: {e}")
            # Fallback for this medication
            medication_copy = medication.copy()
            fallback_url = f"https://pharmeasy.in/search/all?name={medicine_name.replace(' ', '%20')}"
            medication_copy.update({
                "url": fallback_url,
                "reason": f"Error during processing: {str(e)}",
                "all_products": [],
                "selection_confidence": 0
            })
            fixed_medications_list.append(medication_copy)
    
    fixed_medications_json = {"medications": fixed_medications_list}
    
    print(f"\n=== Fix Medications Node Output (Model: {model}) ===")
    print(f"Processed {len(fixed_medications_list)} medications")
    for med in fixed_medications_list:
        product_count = len(med.get('all_products', []))
        confidence = med.get('selection_confidence', 0)
        status = "✓" if product_count > 0 else "✗"
        confidence_indicator = f" ({confidence}%)" if confidence > 0 else ""
        print(f"{status} {med.get('name', 'Unknown')}: {product_count} products found{confidence_indicator}")
    print("==================================================")
    
    state["fixed_medications"] = fixed_medications_json
    return state

def fetch_url_summary(url: str, model: str = "gpt-4o-mini") -> str:
    """
    Fetch URL content and generate a brief summary for hover text.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Simple text extraction (basic approach)
        content = response.text
        
        # Extract title and basic content
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
        title = title_match.group(1) if title_match else "Product"
        
        # Look for price and basic info
        price_patterns = [
            r'₹\s*(\d+(?:\.\d{2})?)',
            r'Rs\.?\s*(\d+(?:\.\d{2})?)',
            r'price[^>]*>([^<]*₹[^<]*)',
        ]
        
        price = "Price not available"
        for pattern in price_patterns:
            price_match = re.search(pattern, content, re.IGNORECASE)
            if price_match:
                price = f"₹{price_match.group(1)}"
                break
        
        # Simple summary
        summary = f"{title.strip()} - {price}"
        
        # Limit length
        if len(summary) > 150:
            summary = summary[:147] + "..."
            
        return summary
        
    except Exception as e:
        return f"Product information - Click to view details"

def markdown_to_html(markdown_text: str) -> str:
    """
    Convert markdown to HTML with basic formatting.
    """
    # Basic markdown to HTML conversion
    html = markdown_text
    
    # Headers
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    
    # Bold and italic
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # Line breaks and paragraphs
    html = re.sub(r'\n\n+', '</p><p>', html)
    html = f'<p>{html}</p>'
    
    # Clean up empty paragraphs
    html = re.sub(r'<p>\s*</p>', '', html)
    
    return html

def generate_medications_table(fixed_medications: Dict[str, Any]) -> str:
    """
    Generate HTML table summarizing the fix medications findings.
    """
    medications = fixed_medications.get("medications", [])
    
    if not medications:
        return "<p>No medications found.</p>"
    
    table_html = """
    <table class="medications-summary">
        <thead>
            <tr>
                <th>Original Name</th>
                <th>Matched Product</th>
                <th>Confidence</th>
                <th>Name Similarity</th>
                <th>Category Match</th>
                <th>Status</th>
                <th>URL</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for medication in medications:
        original_name = medication.get("name", "")
        pharmeasy_name = medication.get("pharmeasy_name", "Not found")
        confidence = medication.get("selection_confidence", 0)
        name_similarity = medication.get("name_similarity", "unknown")
        category_match = medication.get("category_match", "unknown")
        url = medication.get("url", "")
        product_count = len(medication.get("all_products", []))
        
        # Determine status
        if confidence > 80:
            status = "✅ High confidence"
            status_class = "status-good"
        elif confidence > 50:
            status = "⚠️ Medium confidence"
            status_class = "status-medium"
        elif product_count > 0:
            status = "⚠️ Low confidence"
            status_class = "status-low"
        else:
            status = "❌ No match"
            status_class = "status-none"
        
        # Check if name was modified
        name_cell = pharmeasy_name
        if pharmeasy_name != original_name and pharmeasy_name != "Not found":
            name_cell = f"{pharmeasy_name} ⚠️"
        
        url_cell = f'<a href="{url}" target="_blank">View</a>' if url else "N/A"
        
        table_html += f"""
            <tr>
                <td><strong>{original_name}</strong></td>
                <td>{name_cell}</td>
                <td class="confidence">{confidence}%</td>
                <td class="similarity-{name_similarity}">{name_similarity.title()}</td>
                <td class="category-{category_match}">{category_match.title()}</td>
                <td class="{status_class}">{status}</td>
                <td>{url_cell}</td>
            </tr>
        """
    
    table_html += """
        </tbody>
    </table>
    """
    
    return table_html

def add_summary_pills_node(state: GraphState, model: str = "gpt-4o-mini") -> GraphState:
    """
    Generate enhanced HTML summary with inline medication pills and summary table.
    """
    print(f"=== Add Summary Pills Node (Model: {model}) ===")
    
    # Get data from state
    markdown_text = state.get("markdown", "")
    diagnoses = state.get("diagnoses", {})
    fixed_medications = state.get("fixed_medications", {})
    
    # Convert markdown to HTML
    print("Converting markdown to HTML...")
    main_content_html = markdown_to_html(markdown_text)
    
    # Add medication pills to the HTML content
    print("Adding medication pills to content...")
    enhanced_html = add_medication_pills_to_html(main_content_html, fixed_medications, model)
    
    # Generate medications summary table
    print("Generating medications summary table...")
    medications_table = generate_medications_table(fixed_medications)
    
    # Create complete HTML document
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Medical Discharge Summary</title>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            
            .main-content {{
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 30px;
            }}
            
            h1, h2, h3 {{
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }}
            
            .medication-pill, .medication-pill-modified {{
                display: inline-block;
                background: linear-gradient(135deg, #e8f5e8, #c8e6c9);
                border: 2px solid #4caf50;
                padding: 4px 10px;
                margin: 2px;
                border-radius: 15px;
                font-size: 12px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
            }}
            
            .medication-pill-modified {{
                background: linear-gradient(135deg, #fff3e0, #ffcc80);
                border-color: #ff9800;
            }}
            
            .medication-pill:hover, .medication-pill-modified:hover {{
                transform: scale(1.05);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }}
            
            .medications-summary {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            
            .medications-summary th,
            .medications-summary td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            
            .medications-summary th {{
                background: linear-gradient(135deg, #3498db, #2980b9);
                color: white;
                font-weight: bold;
            }}
            
            .medications-summary tr:hover {{
                background-color: #f5f5f5;
            }}
            
            .confidence {{
                font-weight: bold;
            }}
            
            .status-good {{ color: #27ae60; }}
            .status-medium {{ color: #f39c12; }}
            .status-low {{ color: #e74c3c; }}
            .status-none {{ color: #95a5a6; }}
            
            .similarity-high {{ color: #27ae60; font-weight: bold; }}
            .similarity-medium {{ color: #f39c12; font-weight: bold; }}
            .similarity-low {{ color: #e74c3c; font-weight: bold; }}
            
            .category-exact {{ color: #27ae60; font-weight: bold; }}
            .category-similar {{ color: #f39c12; font-weight: bold; }}
            .category-different {{ color: #e74c3c; font-weight: bold; }}
            
            .summary-section {{
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            
            .diagnosis-pill {{
                display: inline-block;
                background: linear-gradient(135deg, #ffebee, #ffcdd2);
                border: 2px solid #f44336;
                padding: 6px 12px;
                margin: 4px;
                border-radius: 15px;
                font-size: 14px;
                font-weight: bold;
            }}
            
            .legend {{
                background: #ecf0f1;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            
            .legend h4 {{
                margin-top: 0;
                color: #2c3e50;
            }}
            
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding: 20px;
                background: #34495e;
                color: white;
                border-radius: 8px;
            }}
        </style>
    </head>
    <body>
        <div class="main-content">
            <h1>📋 Medical Discharge Summary</h1>
            {enhanced_html}
        </div>
        
        <div class="summary-section">
            <h2>🔍 Medication Analysis Summary</h2>
            
            <div class="legend">
                <h4>Legend:</h4>
                <p>
                    <span class="medication-pill">💊 Original Name</span> - Exact match found<br>
                    <span class="medication-pill-modified">💊 Original Name ⚠️</span> - Alternative product suggested<br>
                    Hover over pills to see product details
                </p>
            </div>
            
            {medications_table}
            
            <h3>📊 Summary Statistics</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0;">
                <div style="background: #3498db; color: white; padding: 15px; border-radius: 8px; text-align: center;">
                    <h4>Total Medications</h4>
                    <p style="font-size: 24px; margin: 0;">{len(fixed_medications.get("medications", []))}</p>
                </div>
                <div style="background: #27ae60; color: white; padding: 15px; border-radius: 8px; text-align: center;">
                    <h4>High Confidence Matches</h4>
                    <p style="font-size: 24px; margin: 0;">{len([m for m in fixed_medications.get("medications", []) if m.get("selection_confidence", 0) > 80])}</p>
                </div>
                <div style="background: #f39c12; color: white; padding: 15px; border-radius: 8px; text-align: center;">
                    <h4>Alternative Products</h4>
                    <p style="font-size: 24px; margin: 0;">{len([m for m in fixed_medications.get("medications", []) if m.get("modified_name")])}</p>
                </div>
                <div style="background: #e74c3c; color: white; padding: 15px; border-radius: 8px; text-align: center;">
                    <h4>No Matches Found</h4>
                    <p style="font-size: 24px; margin: 0;">{len([m for m in fixed_medications.get("medications", []) if len(m.get("all_products", [])) == 0])}</p>
                </div>
            </div>
            
            <h3>🏥 Diagnoses</h3>
            <div>
                {"".join([f'<span class="diagnosis-pill">{d}</span>' for d in diagnoses.get("diagnoses", [])])}
            </div>
        </div>
        
        <div class="footer">
            <p>Generated with {model} | Enhanced Medical Document Processing</p>
            <p><small>Medication information sourced from PharmeEasy.in</small></p>
        </div>
    </body>
    </html>
    """
    
    print("Enhanced HTML summary generated with:")
    print(f"- {len(fixed_medications.get('medications', []))} medications processed")
    print(f"- {len([m for m in fixed_medications.get('medications', []) if m.get('selection_confidence', 0) > 80])} high confidence matches")
    print(f"- Interactive pills and hover summaries added")
    print(f"- Comprehensive summary table included")
    print("=======================================")
    
    state["html_summary"] = html_content
    return state

class AppGraph:
    """Wrapper class for the LangGraph workflow with convenience methods."""
    
    def __init__(self):
        self.state = {}
    
    def run_node(self, node_name: str, input_data=None, model: str = "gpt-4o-mini"):
        """
        Run a specific node in the workflow.
        """
        print(f"Running node: {node_name} with model: {model}")
        
        if node_name == "OCR" and input_data:
            self.state["images"] = input_data
        
        if node_name == "OCR":
            self.state = ocr_node(self.state, model)
            return self.state.get("markdown", "")
        elif node_name == "ExtractDiagnoses":
            self.state = extract_diagnoses_node(self.state, model)
            return self.state.get("diagnoses", {})
        elif node_name == "ExtractMedications":
            self.state = extract_medications_node(self.state, model)
            return self.state.get("medications", {})
        elif node_name == "FixMedications":
            self.state = fix_medications_node(self.state, model)
            return self.state.get("fixed_medications", {})
        elif node_name == "AddSummaryPills":
            self.state = add_summary_pills_node(self.state, model)
            return self.state.get("html_summary", "")
        else:
            raise ValueError(f"Unknown node: {node_name}")
    
    def get_state(self):
        """Get the current workflow state."""
        return self.state
    
    def reset_state(self):
        """Reset the workflow state."""
        self.state = {}

# Create the app_graph instance
app_graph = AppGraph()