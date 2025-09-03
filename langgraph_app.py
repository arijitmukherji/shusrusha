from langgraph.graph import StateGraph
from typing import TypedDict, List, Dict, Any
import openai
import base64
import os
import json
import requests
import re
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import random

# Define the state structure
class GraphState(TypedDict):
    images: List[str]
    markdown: str
    diagnoses: Dict[str, Any]
    medications: Dict[str, Any]
    fixed_medications: Dict[str, Any]
    html_summary: str

# Thread-safe rate limiter for API calls
class RateLimiter:
    def __init__(self, max_calls_per_second=2):
        self.max_calls_per_second = max_calls_per_second
        self.min_interval = 1.0 / max_calls_per_second
        self.last_call_time = 0
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        with self.lock:
            current_time = time.time()
            time_since_last_call = current_time - self.last_call_time
            if time_since_last_call < self.min_interval:
                sleep_time = self.min_interval - time_since_last_call
                time.sleep(sleep_time)
            self.last_call_time = time.time()

# Global rate limiters
pharmeasy_rate_limiter = RateLimiter(max_calls_per_second=1)  # Very conservative for web scraping
openai_rate_limiter = RateLimiter(max_calls_per_second=10)    # OpenAI can handle more

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

def ocr_node(state: GraphState, model: str = "gpt-4o-mini", api_key: str = None) -> GraphState:
    """
    Process images and extract text using GPT-4 Vision.
    """
    system_prompt = """Task. You are an expert medical assistant working in a hospital located 
    in Kolkata, India. Transcribe this discharge summary issued to a patient exactly 
    (i.e. preserve all sections/headers/order/ and all written text). If in doubt about some unclear writing,
      try to match with terms that make sense in an India context, for medical field and 
      relevant diagnoses, and check medications against India availability. Do not change
      ocr-detected medicine name in non-trivial ways (e.g. do not change Pan => Rantac which
      has many more and different characters). Then output a 
      simple markdown document with all the contents with the same content as the original. For 
      prescribed medications, "Tab" is often written to look like "76" """
    
    client = openai.OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
    
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

def extract_diagnoses_node(state: GraphState, model: str = "gpt-4o-mini", api_key: str = None) -> GraphState:
    """
    Extract diagnoses and lab tests from the markdown text.
    """
    markdown_text = state.get("markdown", "")
    
    system_prompt = """You are an expert medical doctor practising in Kolkata India. You have been given a hospital discharge report of a patient in simple mardown text format. Your job is to identify all the relevant medical terms in the document related to a) diagnosis names b) lab test names from the document. Ignore all medicine names. Keep in mind common terminology used in that part of the world. Return a JSON structure of the form
{"diagnoses": ["diagnosis term 1", "diagnosis term 2", ...], "lab_tests":["lab test name 1", "lab test name 2", ...]}"""
    
    client = openai.OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
    
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

def extract_medications_node(state: GraphState, model: str = "gpt-4o-mini", api_key: str = None) -> GraphState:
    """
    Extract medications from the markdown text.
    """
    markdown_text = state.get("markdown", "")
    
    system_prompt = """You are an expert medical doctor practising in Kolkata India. You have been given a hospital discharge report of a patient in simple mardown text format. Your job is to identify all the relevant medications from the document along with instructions. In case of difficulty identifying a medication, make sure the names match actual medications used in that part of the world. Return a JSON structure of the form
{"medications": [{"name":"paracetamol xr", "form":"tablet", "strength":"5 mg", "instructions":"Twice daily", "duration":"continue"}, {"name":"atorvastatin", "form":"syrup", "strength":"10 ml", "instructions":"as needed", "duration":"as needed"}, {"name":"medicine_3", "form":"powder", "strength":"1 pouch", "instructions":"BID", "duration":"10 days"}]}.
The "name" fields should only contain the medicine name e.g. "Rantac XR")
and not contain other information like its strength or form factor (tab/table, cap/capsure, 
syr/syrup, pdr/powder etc.). Finally append a small description to the instructions if they
are not easily understandable by a layman"""

    client = openai.OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
    
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

def fetch_pharmeasy_content(medicine_name: str, max_retries: int = 3) -> str:
    """
    Fetch the HTML content from PharmeEasy search page with rate limiting and retry logic.
    """
    for attempt in range(max_retries):
        try:
            # Rate limiting to avoid being blocked
            pharmeasy_rate_limiter.wait_if_needed()
            
            # Add random delay to avoid looking like a bot
            if attempt > 0:
                delay = random.uniform(1, 3)
                print(f"Retry {attempt + 1} for {medicine_name}, waiting {delay:.1f}s...")
                time.sleep(delay)
            
            encoded_medicine = quote(medicine_name)
            search_url = f"https://pharmeasy.in/search/all?name={encoded_medicine}"
            
            # Create a fresh session for each request to avoid connection issues
            session = requests.Session()
            
            headers = {
                'User-Agent': f'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            session.headers.update(headers)
            
            print(f"Fetching: {search_url} (attempt {attempt + 1})")
            
            response = session.get(
                search_url, 
                timeout=20,  # Increased timeout
                allow_redirects=True
            )
            
            # Check for rate limiting or blocking
            if response.status_code == 429:
                print(f"Rate limited for {medicine_name}, waiting before retry...")
                time.sleep(5)
                continue
            elif response.status_code == 403:
                print(f"Access forbidden for {medicine_name}, trying with different headers...")
                # Try with different user agent
                headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                session.headers.update(headers)
                continue
            
            response.raise_for_status()
            
            content = response.text
            print(f"Successfully fetched {len(content)} characters from PharmeEasy for {medicine_name}")
            
            # Close the session
            session.close()
            
            return content
            
        except requests.exceptions.Timeout:
            print(f"Timeout error for {medicine_name} (attempt {attempt + 1})")
        except requests.exceptions.ConnectionError:
            print(f"Connection error for {medicine_name} (attempt {attempt + 1})")
        except requests.exceptions.RequestException as e:
            print(f"Request error for {medicine_name} (attempt {attempt + 1}): {e}")
        except Exception as e:
            print(f"Unexpected error fetching {medicine_name} (attempt {attempt + 1}): {e}")
        
        # Close session if it exists
        try:
            session.close()
        except:
            pass
    
    print(f"Failed to fetch content for {medicine_name} after {max_retries} attempts")
    return ""

def parse_pharmeasy_products(html_content: str, model: str = "gpt-4o-mini", max_retries: int = 3, api_key: str = None) -> List[Dict[str, str]]:
    """
    Use LLM to parse Pharmeasy HTML and extract product listings with retry logic.
    Also handles JSON data embedded in the page.
    """
    
    # First, try to extract products from JSON data embedded in the page
    json_products = extract_json_products_from_html(html_content)
    if json_products:
        print(f"Extracted {len(json_products)} products from embedded JSON data")
        return json_products
    
    # Fallback to LLM parsing for HTML elements
    for attempt in range(max_retries):
        try:
            # Rate limiting for OpenAI API
            openai_rate_limiter.wait_if_needed()
            
            if attempt > 0:
                print(f"Retrying OpenAI API call for HTML parsing (attempt {attempt + 1})")
                time.sleep(random.uniform(0.5, 1.5))
            
            client = openai.OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
            
            system_prompt = """You are an expert web scraper. Parse this HTML content from Pharmeasy.in search results.

Look for product listings in the main body of the page and extract up to 10 products. For each product, extract:
- name: The product name/title
- url: The product URL (if relative path, prepend "https://pharmeasy.in")

Look for patterns like:
- Product cards or containers
- Links to product pages (often containing "/online-medicine-order/" or "/medicines/")
- Product names in headings, spans, or divs
- Medicine names and dosages
- JSON data containing product information

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
            
            print(f"Extracted {len(cleaned_products)} products from Pharmeasy page")
            return cleaned_products
            
        except openai.RateLimitError:
            print(f"OpenAI rate limit hit, waiting before retry (attempt {attempt + 1})")
            time.sleep(2 ** attempt)  # Exponential backoff
        except openai.APIError as e:
            print(f"OpenAI API error in HTML parsing (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
        except json.JSONDecodeError as e:
            print(f"JSON decode error in HTML parsing (attempt {attempt + 1}): {e}")
        except Exception as e:
            print(f"Unexpected error in HTML parsing (attempt {attempt + 1}): {e}")
    
    print(f"Failed to parse Pharmeasy HTML after {max_retries} attempts")
    return []

def extract_json_products_from_html(html_content: str) -> List[Dict[str, str]]:
    """
    Extract product data from JSON embedded in PharmeEasy HTML.
    """
    import json
    import re
    
    try:
        # Look for JSON data in script tags or inline JSON
        # PharmeEasy often embeds product data in __NEXT_DATA__ or similar structures
        
        # Pattern 1: Look for __NEXT_DATA__ JSON
        next_data_pattern = r'__NEXT_DATA__["\']?\s*[=:]\s*({.*?})\s*(?:;|\n|</script>)'
        matches = re.findall(next_data_pattern, html_content, re.DOTALL)
        
        for match in matches:
            try:
                data = json.loads(match)
                products = extract_products_from_json(data)
                if products:
                    return products
            except json.JSONDecodeError:
                continue
        
        # Pattern 2: Look for product arrays directly in JSON
        product_pattern = r'"products"\s*:\s*\[([^\]]*"name"[^\]]*)\]'
        matches = re.findall(product_pattern, html_content, re.DOTALL)
        
        for match in matches:
            try:
                # Try to parse the products array
                products_json = f'[{match}]'
                products_data = json.loads(products_json)
                
                extracted_products = []
                for product in products_data:
                    if isinstance(product, dict) and 'name' in product:
                        name = product.get('name', '')
                        slug = product.get('slug', '')
                        product_id = product.get('productId', '')
                        
                        # Construct URL
                        if slug:
                            url = f"https://pharmeasy.in/online-medicine-order/{slug}"
                        elif product_id:
                            url = f"https://pharmeasy.in/online-medicine-order?medicine_id={product_id}"
                        else:
                            continue
                        
                        if name and url:
                            extracted_products.append({
                                "name": name,
                                "url": url
                            })
                
                if extracted_products:
                    return extracted_products[:10]  # Limit to 10 products
                    
            except json.JSONDecodeError:
                continue
        
        # Pattern 3: Look for individual product objects with name and slug
        individual_product_pattern = r'{[^}]*"name"\s*:\s*"([^"]*)"[^}]*"slug"\s*:\s*"([^"]*)"[^}]*}'
        matches = re.findall(individual_product_pattern, html_content)
        
        if matches:
            extracted_products = []
            for name, slug in matches[:10]:  # Limit to 10
                if name and slug:
                    url = f"https://pharmeasy.in/online-medicine-order/{slug}"
                    extracted_products.append({
                        "name": name,
                        "url": url
                    })
            
            if extracted_products:
                return extracted_products
        
        return []
        
    except Exception as e:
        print(f"Error extracting JSON products: {e}")
        return []

def extract_products_from_json(data: dict) -> List[Dict[str, str]]:
    """
    Recursively extract product information from nested JSON data.
    """
    products = []
    
    def find_products(obj, path=""):
        if isinstance(obj, dict):
            # Check if this looks like a product object
            if 'name' in obj and 'slug' in obj:
                name = obj.get('name', '')
                slug = obj.get('slug', '')
                product_id = obj.get('productId', '')
                
                if name and (slug or product_id):
                    if slug:
                        url = f"https://pharmeasy.in/online-medicine-order/{slug}"
                    else:
                        url = f"https://pharmeasy.in/online-medicine-order?medicine_id={product_id}"
                    
                    products.append({
                        "name": name,
                        "url": url
                    })
            
            # Continue searching in nested objects
            for key, value in obj.items():
                find_products(value, f"{path}.{key}" if path else key)
                
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                find_products(item, f"{path}[{i}]" if path else f"[{i}]")
    
    find_products(data)
    return products[:10]  # Limit to 10 products

def wrap_medication_items_in_lists(html_content: str) -> str:
    """
    Find consecutive medication list items and wrap them in proper <ul> tags.
    """
    # Find all medication items
    pattern = r'(<li class="medication-item">[^<]*(?:<[^>]*>[^<]*)*</li>)'
    
    def replace_with_list(match):
        return f'<ul class="medication-list">{match.group(1)}</ul>'
    
    # Replace single medication items with wrapped lists
    html_content = re.sub(pattern, replace_with_list, html_content)
    
    # Merge consecutive medication lists
    merge_pattern = r'</ul>\s*<ul class="medication-list">'
    html_content = re.sub(merge_pattern, '', html_content)
    
    return html_content

def add_medication_pills_to_html(html_content: str, fixed_medications: Dict[str, Any], model: str = "gpt-4o-mini") -> str:
    """
    Add visual pills next to medications in the HTML content, converting to list items.
    """
    medications = fixed_medications.get("medications", [])
    
    for medication in medications:
        original_name = medication.get("name", "")
        pharmeasy_name = medication.get("pharmeasy_name", "")
        url = medication.get("url", "")
        confidence = medication.get("selection_confidence", 0)
        modified_name = medication.get("modified_name", "")
        selection_reasoning = medication.get("selection_reasoning", "")
        reason = medication.get("reason", "")
        
        if not original_name:
            continue
        
        # Create tooltip based on selection reasoning or reason for change
        tooltip_text = ""
        if selection_reasoning:
            tooltip_text = selection_reasoning
        elif reason:
            tooltip_text = reason
        elif pharmeasy_name and pharmeasy_name != "Not found":
            tooltip_text = f"Found matching product: {pharmeasy_name}"
        else:
            tooltip_text = f"Search for {original_name} on Pharmeasy"
        
        # Limit tooltip length
        if len(tooltip_text) > 200:
            tooltip_text = tooltip_text[:197] + "..."
        
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
        
        warning_icon = " ⚠" if name_modified else ""
        
        # Create smaller, more subtle pill HTML
        pill_class = "medication-pill-modified" if name_modified else "medication-pill"
        confidence_indicator = f"<small style='color: #999; font-size: 0.7em;'> ({confidence}%)</small>" if confidence > 0 else ""
        
        pill_html = f'''<span class="{pill_class}" title="{tooltip_text}">
            <a href="{url}" target="_blank" style="text-decoration: none; color: inherit;">
                💊 {display_names}{warning_icon}
            </a>
        </span>{confidence_indicator}'''

        # Find and replace medication name in HTML - convert to list item
        replacements_made = 0
        
        # Method 1: Exact word boundary match
        pattern1 = r'\b' + re.escape(original_name) + r'\b'
        if re.search(pattern1, html_content, re.IGNORECASE):
            # Replace with list item
            html_content = re.sub(pattern1, f'<li class="medication-item">{original_name} {pill_html}</li>', html_content, count=1, flags=re.IGNORECASE)
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
                        html_content = html_content[:pos] + f'<li class="medication-item">{variant} {pill_html}</li>' + html_content[pos + len(variant):]
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
                        html_content = re.sub(pattern, f'<li class="medication-item">{part} {pill_html}</li>', html_content, count=1, flags=re.IGNORECASE)
                        replacements_made += 1
                        break
        
        # Debug output
        if replacements_made == 0:
            print(f"⚠️ Warning: Could not find medication '{original_name}' in HTML content")
        else:
            print(f"✓ Added pill for: {original_name} ({'modified' if name_modified else 'exact'})")
    
    # After all medications are processed, wrap orphaned list items in proper lists
    html_content = wrap_medication_items_in_lists(html_content)
    
    return html_content

def add_summary_pills_node(state: GraphState, model: str = "gpt-4o-mini", api_key: str = None) -> GraphState:
    """
    Generate enhanced HTML summary with inline medication pills as list items.
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
    #print("Adding medication pills to content...")
    #enhanced_html = add_medication_pills_to_html(main_content_html, fixed_medications, model)
    enhanced_html = main_content_html

    # Generate medications summary table
    print("Generating medications summary table...")
    medications_table = generate_medications_table(fixed_medications)
    
    # Create complete HTML document with list-based medication display
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
            
            .medication-list {{
                list-style-type: none;
                padding-left: 0;
                margin: 15px 0;
                background: #f8f9fa;
                border-left: 4px solid #007bff;
                border-radius: 4px;
            }}
            
            .medication-item {{
                padding: 8px 15px;
                margin: 0;
                border-bottom: 1px solid #e9ecef;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }}
            
            .medication-item:last-child {{
                border-bottom: none;
            }}
            
            .medication-pill, .medication-pill-modified {{
                display: inline-block;
                background: rgba(76, 175, 80, 0.1);
                border: 1px solid rgba(76, 175, 80, 0.3);
                padding: 2px 6px;
                margin-left: 8px;
                border-radius: 8px;
                font-size: 0.75em;
                font-weight: normal;
                cursor: pointer;
                transition: all 0.2s ease;
                opacity: 0.8;
            }}
            
            .medication-pill-modified {{
                background: rgba(255, 152, 0, 0.1);
                border-color: rgba(255, 152, 0, 0.3);
            }}
            
            .medication-pill:hover, .medication-pill-modified:hover {{
                opacity: 1;
                transform: scale(1.02);
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
                    <span class="medication-pill-modified">💊 Original Name ⚠</span> - Alternative product suggested<br>
                    <small>Hover over pills to see product details</small>
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
            <p><small>Medication information sourced from Pharmeasy.in</small></p>
        </div>
    </body>
    </html>
    """
    
    print("Enhanced HTML summary generated with:")
    print(f"- {len(fixed_medications.get('medications', []))} medications processed")
    print(f"- {len([m for m in fixed_medications.get('medications', []) if m.get('selection_confidence', 0) > 80])} high confidence matches")
    print(f"- Medications displayed as list items")
    print(f"- Subtle inline pills and hover summaries added")
    print("=======================================")
    
    state["html_summary"] = html_content
    return state

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

def select_best_product_match(medicine_name: str, products: List[Dict[str, str]], diagnoses: List[str], model: str = "gpt-4o-mini", max_retries: int = 3, medication_details: Dict[str, Any] = None, api_key: str = None) -> Dict[str, Any]:
    """
    Use hierarchical scoring to select the best matching product based on:
    1. Exact Name match (ignoring non-alphabetic characters)
    2. Strength matching
    3. Name similarity
    4. Category similarity
    """
    def normalize_name_for_exact_match(text: str) -> str:
        """Normalize text by removing non-alphabetic characters and converting to lowercase."""
        import re
        return re.sub(r'[^a-zA-Z]', '', text).lower()

    def extract_strength(text: str) -> str:
        """Extract numerical strength from text (e.g., '150mg' -> '150')."""
        import re
        matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:mg|ml|g|mcg|units?|iu)', text.lower())
        return matches[0] if matches else ""

    def calculate_hierarchical_score(medicine_name: str, product_name: str, medicine_strength: str, product_text: str) -> tuple:
        """
        Calculate hierarchical score based on the specified priority order.
        Returns (total_score, breakdown) where breakdown shows individual scores.
        """
        
        # 1. EXACT NAME MATCH (40 points max)
        normalized_medicine = normalize_name_for_exact_match(medicine_name)
        normalized_product = normalize_name_for_exact_match(product_name)
        
        exact_name_score = 0
        if normalized_medicine in normalized_product or normalized_product in normalized_medicine:
            exact_name_score = 40  # Full points for exact match
        elif len(normalized_medicine) > 3 and len(normalized_product) > 3:
            # Check for substantial overlap for very close matches
            shorter = normalized_medicine if len(normalized_medicine) < len(normalized_product) else normalized_product
            longer = normalized_product if len(normalized_medicine) < len(normalized_product) else normalized_medicine
            overlap_ratio = sum(1 for i in range(len(shorter)) if i < len(longer) and shorter[i] == longer[i]) / len(shorter)
            if overlap_ratio > 0.8:
                exact_name_score = 30  # High points for very close match
        
        # 2. STRENGTH MATCHING (30 points max)
        strength_score = 0
        extracted_medicine_strength = extract_strength(medicine_strength) if medicine_strength else ""
        extracted_product_strength = extract_strength(product_text)
        
        if extracted_medicine_strength and extracted_product_strength:
            try:
                med_val = float(extracted_medicine_strength)
                prod_val = float(extracted_product_strength)
                if med_val == prod_val:
                    strength_score = 30  # Exact strength match
                elif abs(med_val - prod_val) / max(med_val, prod_val) <= 0.1:  # Within 10%
                    strength_score = 20  # Close strength match
                elif abs(med_val - prod_val) / max(med_val, prod_val) <= 0.5:  # Within 50%
                    strength_score = 10  # Partial strength match
            except ValueError:
                pass
        elif not extracted_medicine_strength and extracted_product_strength:
            strength_score = 15  # Some strength info is better than none
        
        # 3. NAME SIMILARITY (20 points max)
        name_similarity_score = 0
        # Simple similarity calculation
        medicine_words = set(medicine_name.lower().split())
        product_words = set(product_name.lower().split())
        
        if medicine_words and product_words:
            intersection = medicine_words.intersection(product_words)
            union = medicine_words.union(product_words)
            jaccard_similarity = len(intersection) / len(union) if union else 0
            name_similarity_score = int(jaccard_similarity * 20)
        
        # 4. CATEGORY SIMILARITY (10 points max)
        category_score = 0
        # Check for common pharmaceutical terms
        medicine_lower = medicine_name.lower()
        product_lower = product_name.lower()
        
        # Common drug categories and forms
        categories = ['tablet', 'syrup', 'capsule', 'injection', 'cream', 'ointment', 'drops']
        forms = ['strip', 'bottle', 'vial', 'tube']
        
        medicine_categories = [cat for cat in categories if cat in medicine_lower]
        product_categories = [cat for cat in categories if cat in product_lower]
        
        medicine_forms = [form for form in forms if form in medicine_lower]
        product_forms = [form for form in forms if form in product_lower]
        
        if set(medicine_categories).intersection(set(product_categories)):
            category_score += 5  # Same category
        if set(medicine_forms).intersection(set(product_forms)):
            category_score += 5  # Same form
        
        total_score = exact_name_score + strength_score + name_similarity_score + category_score
        
        breakdown = {
            "exact_name": exact_name_score,
            "strength": strength_score,
            "name_similarity": name_similarity_score,
            "category": category_score,
            "total": total_score
        }
        
        return total_score, breakdown

    # Pre-analyze all products with hierarchical scoring
    product_scores = []
    medicine_strength = medication_details.get('strength', '') if medication_details else ''
    
    for i, product in enumerate(products):
        score, breakdown = calculate_hierarchical_score(
            medicine_name, 
            product['name'], 
            medicine_strength, 
            product['name']
        )
        product_scores.append({
            "index": i,
            "score": score,
            "breakdown": breakdown,
            "product": product
        })
    
    # Sort by score (highest first)
    product_scores.sort(key=lambda x: x["score"], reverse=True)
    
    # Get the best match
    best_match = product_scores[0] if product_scores else None
    
    if not best_match:
        return {
            "product": products[0] if products else None,
            "analysis": {"reasoning": "No products to evaluate", "confidence_score": 0},
            "success": False
        }
    
    # Convert score to confidence percentage
    max_possible_score = 100  # 40 + 30 + 20 + 10
    confidence_percentage = min(100, int((best_match["score"] / max_possible_score) * 100))
    
    # Ensure minimum confidence for exact name matches
    if best_match["breakdown"]["exact_name"] >= 30:  # Strong exact match
        confidence_percentage = max(confidence_percentage, 85)
    elif best_match["breakdown"]["exact_name"] >= 20:  # Good exact match
        confidence_percentage = max(confidence_percentage, 75)
    
    # Build detailed reasoning
    breakdown = best_match["breakdown"]
    reasoning_parts = []
    
    if breakdown["exact_name"] >= 30:
        reasoning_parts.append(f"Exact name match found ({breakdown['exact_name']}/40 points)")
    elif breakdown["exact_name"] > 0:
        reasoning_parts.append(f"Partial name match ({breakdown['exact_name']}/40 points)")
    else:
        reasoning_parts.append("No exact name match (0/40 points)")
    
    if breakdown["strength"] >= 25:
        reasoning_parts.append(f"Exact strength match ({breakdown['strength']}/30 points)")
    elif breakdown["strength"] > 0:
        reasoning_parts.append(f"Partial strength match ({breakdown['strength']}/30 points)")
    else:
        reasoning_parts.append("No strength match (0/30 points)")
    
    reasoning_parts.append(f"Name similarity: {breakdown['name_similarity']}/20 points")
    reasoning_parts.append(f"Category similarity: {breakdown['category']}/10 points")
    reasoning_parts.append(f"Total score: {breakdown['total']}/100")
    
    detailed_reasoning = ". ".join(reasoning_parts)
    
    # Determine categorical ratings
    name_similarity = "high" if breakdown["exact_name"] >= 30 else ("medium" if breakdown["exact_name"] >= 10 else "low")
    strength_match = "exact" if breakdown["strength"] >= 25 else ("partial" if breakdown["strength"] >= 10 else "none")
    category_match = "exact" if breakdown["category"] >= 8 else ("similar" if breakdown["category"] >= 4 else "different")
    
    # Get alternative suggestions (top 3 excluding the selected one)
    alternatives = [item["index"] for item in product_scores[1:4]]
    
    analysis = {
        "confidence_score": confidence_percentage,
        "reasoning": detailed_reasoning,
        "name_similarity": name_similarity,
        "strength_match": strength_match,
        "form_match": "unknown",  # This could be enhanced if needed
        "category_match": category_match,
        "hierarchical_breakdown": breakdown,
        "alternative_suggestions": alternatives
    }
    
    print(f"  🎯 Hierarchical Scoring for '{medicine_name}':")
    print(f"     Selected: {best_match['product']['name']}")
    print(f"     Score breakdown: {breakdown}")
    print(f"     Final confidence: {confidence_percentage}%")
    
    return {
        "product": best_match["product"],
        "analysis": analysis,
        "success": True
    }

def process_single_medication(medication: Dict[str, Any], diagnoses_list: List[str], model: str, medication_index: int, api_key: str = None) -> Dict[str, Any]:
    """
    Process a single medication to find matching products on Pharmeasy.
    This function is designed to be run in parallel.
    """
    base_medicine_name = medication.get('name', 'Unknown')
    
    # Build enhanced search term with strength and form
    search_terms = [base_medicine_name.strip()]
    
    # Extract numerical strength (e.g., "40mg", "5ml", "100")
    strength = medication.get('strength', '').strip()
    if strength:
        # Extract only the numerical part, exclude units (mg, ml, etc.)
        import re
        strength_match = re.search(r'(\d+\.?\d*)', strength.lower())
        if strength_match:
            numerical_strength = strength_match.group(1)
            # Only add if it's not already in the medicine name and is meaningful
            if numerical_strength and numerical_strength not in base_medicine_name.lower():
                search_terms.append(numerical_strength)
    
    # Add form factor if available and not already in name
    form = medication.get('form', '').strip()
    if form and form.lower() not in base_medicine_name.lower():
        search_terms.append(form.lower())
    
    # Construct final search term
    enhanced_medicine_name = ' '.join(search_terms)
    
    print(f"\n🚀 STARTING: [{medication_index + 1}] {base_medicine_name}")
    if enhanced_medicine_name != base_medicine_name:
        print(f"   🔍 Enhanced search: '{enhanced_medicine_name}'")
    
    try:
        # Fetch Pharmeasy page content using enhanced search term
        html_content = fetch_pharmeasy_content(enhanced_medicine_name)
        
        # Create enhanced medication object
        medication_copy = medication.copy()
        
        if html_content:
            # Parse products from the HTML
            products = parse_pharmeasy_products(html_content, model, api_key=api_key)
            
            if products:
                print(f"Found {len(products)} products, selecting best match...")
                
                # Use LLM to select the best matching product
                selection_result = select_best_product_match(
                    base_medicine_name,  # Use original name for LLM analysis
                    products, 
                    diagnoses_list, 
                    model,
                    medication_details=medication,  # Pass full medication details
                    api_key=api_key
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
                        "strength_match": analysis.get("strength_match", "unknown"),  # NEW
                        "form_match": analysis.get("form_match", "unknown"),          # NEW
                        "dosage_appropriateness": analysis.get("dosage_appropriateness", "unknown"),
                        "category_match": analysis.get("category_match", "unknown")
                    })
                    
                    # Check if name differs significantly
                    original_lower = base_medicine_name.lower()
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
                fallback_url = f"https://pharmeasy.in/search/all?name={base_medicine_name.replace(' ', '%20')}"  # Use original name for fallback
                medication_copy.update({
                    "url": fallback_url,
                    "reason": "No products found in page content, using search URL",
                    "all_products": [],
                    "selection_confidence": 0
                })
                print(f"✗ No products extracted from page content")
        else:
            # Failed to fetch content
            fallback_url = f"https://pharmeasy.in/search/all?name={base_medicine_name.replace(' ', '%20')}"  # Use original name for fallback
            medication_copy.update({
                "url": fallback_url,
                "reason": "Failed to fetch page content, using search URL",
                "all_products": [],
                "selection_confidence": 0
            })
            print(f"✗ Failed to fetch page content")
        
        return medication_copy
        
    except Exception as e:
        print(f"✗ Error processing {base_medicine_name}: {e}")  # Use original name for error message
        # Fallback for this medication
        medication_copy = medication.copy()
        fallback_url = f"https://pharmeasy.in/search/all?name={base_medicine_name.replace(' ', '%20')}"  # Use original name for fallback
        medication_copy.update({
            "url": fallback_url,
            "reason": f"Error during processing: {str(e)}",
            "all_products": [],
            "selection_confidence": 0
        })
        return medication_copy

def fix_medications_node(state: GraphState, model: str = "gpt-4o-mini", api_key: str = None) -> GraphState:
    """
    Fetch Pharmeasy content for each medication and use LLM to select the best matching product.
    Uses parallel processing to significantly reduce processing time.
    """
    medications_data = state.get("medications", {"medications": []})
    diagnoses_data = state.get("diagnoses", {"diagnoses": [], "lab_tests": []})
    diagnoses_list = diagnoses_data.get("diagnoses", [])
    
    medications_list = medications_data.get("medications", [])
    
    if not medications_list:
        print("No medications to process")
        state["fixed_medications"] = {"medications": []}
        return state
    
    print(f"\n=== Fix Medications Node - Parallel Processing (Model: {model}) ===")
    print(f"Processing {len(medications_list)} medications in parallel...")
    
    # Use ThreadPoolExecutor for parallel processing
    # Increased concurrency but with rate limiting to avoid overwhelming servers
    max_workers = min(5, len(medications_list))  # Max 5 concurrent requests with rate limiting
    fixed_medications_list = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all medication processing tasks with rate limiting
        future_to_index = {}
        future_to_medication = {}
        
        print(f"Submitting {len(medications_list)} medications with rate limiting (1 per second)...")
        
        for i, medication in enumerate(medications_list):
            medicine_name = medication.get('name', f'Unknown_{i}')
            
            # Rate limiting: Start maximum 1 lookup per second
            if i > 0:  # Don't delay the first submission
                time.sleep(1.0)  # 1 second delay between submissions
                print(f"⏱️ Rate limit delay: Starting medication {i+1} ({medicine_name})")
            
            future = executor.submit(
                process_single_medication, 
                medication, 
                diagnoses_list, 
                model, 
                i,
                api_key
            )
            future_to_index[future] = i
            future_to_medication[future] = medicine_name
        
        # Print all medications that are now being processed in parallel
        active_medications = list(future_to_medication.values())
        print(f"\n🔄 PARALLEL PROCESSING STARTED - {len(active_medications)} medications:")
        for i, med_name in enumerate(active_medications):
            print(f"   [{i+1}] {med_name}")
        print(f"   Using {max_workers} parallel workers with 1-second rate limiting\n")
        
        # Collect results as they complete
        results = [None] * len(medications_list)  # Pre-allocate list to maintain order
        completed_count = 0
        failed_count = 0
        
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                result = future.result(timeout=120)  # 2 minute timeout per medication
                results[index] = result
                completed_count += 1
                
                # Progress indicator
                medicine_name = result.get('name', 'Unknown')
                confidence = result.get('selection_confidence', 0)
                product_count = len(result.get('all_products', []))
                status = "✓" if product_count > 0 else "✗"
                
                if product_count > 0:
                    print(f"[{completed_count}/{len(medications_list)}] {status} {medicine_name} - {confidence}% confidence ({product_count} products)")
                else:
                    print(f"[{completed_count}/{len(medications_list)}] {status} {medicine_name} - No products found")
                
            except Exception as e:
                failed_count += 1
                print(f"✗ Error processing medication at index {index}: {e}")
                # Create fallback result
                original_medication = medications_list[index]
                medicine_name = original_medication.get('name', 'Unknown')
                fallback_url = f"https://pharmeasy.in/search/all?name={medicine_name.replace(' ', '%20')}"
                fallback_result = original_medication.copy()
                fallback_result.update({
                    "url": fallback_url,
                    "reason": f"Parallel processing error: {str(e)}",
                    "all_products": [],
                    "selection_confidence": 0,
                    "pharmeasy_name": "Error - fallback URL"
                })
                results[index] = fallback_result
                completed_count += 1
    
    # Filter out any None results (shouldn't happen, but safety check)
    fixed_medications_list = [result for result in results if result is not None]
    
    fixed_medications_json = {"medications": fixed_medications_list}
    
    print(f"\n=== Parallel Processing Complete (Model: {model}) ===")
    print(f"Processed {len(fixed_medications_list)} medications using {max_workers} parallel workers with rate limiting")
    
    if failed_count > 0:
        print(f"⚠️ {failed_count} medications failed during processing and used fallback URLs")
    
    # Summary statistics
    successful_matches = sum(1 for med in fixed_medications_list if len(med.get('all_products', [])) > 0)
    high_confidence = sum(1 for med in fixed_medications_list if med.get('selection_confidence', 0) > 80)
    medium_confidence = sum(1 for med in fixed_medications_list if 50 <= med.get('selection_confidence', 0) <= 80)
    fallback_urls = sum(1 for med in fixed_medications_list if 'fallback' in med.get('reason', '').lower() or 'error' in med.get('reason', '').lower())
    
    print(f"Results Summary:")
    print(f"- Successful matches: {successful_matches}/{len(fixed_medications_list)}")
    print(f"- High confidence (>80%): {high_confidence}")
    print(f"- Medium confidence (50-80%): {medium_confidence}")
    print(f"- Low/No confidence: {len(fixed_medications_list) - high_confidence - medium_confidence}")
    print(f"- Fallback URLs (errors): {fallback_urls}")
    
    # Detailed per-medication summary
    for med in fixed_medications_list:
        product_count = len(med.get('all_products', []))
        confidence = med.get('selection_confidence', 0)
        is_fallback = 'fallback' in med.get('reason', '').lower() or 'error' in med.get('reason', '').lower()
        
        if is_fallback:
            status = "⚠"
            confidence_indicator = " (fallback)"
        else:
            status = "✓" if product_count > 0 else "✗"
            confidence_indicator = f" ({confidence}%)" if confidence > 0 else ""
        
        pharmeasy_name = med.get('pharmeasy_name', 'No match')
        print(f"- {status} {med.get('name')} → {pharmeasy_name}{confidence_indicator}")
    
    print("====================================")
    
    state["fixed_medications"] = fixed_medications_json
    return state

# At the end of the file, add the app_graph instance
class AppGraph:
    def __init__(self):
        self.state = {}
    
    def run_node(self, node_name: str, input_data=None, model: str = "gpt-4o-mini", api_key: str = None):
        """
        Run a specific node in the graph with the given input data.
        """
        if input_data is not None:
            if node_name == "OCR":
                self.state = ocr_node({"images": input_data}, model, api_key=api_key)
                return self.state.get("markdown", "")
            else:
                # For other nodes, input_data might be used differently
                pass
        
        if node_name == "OCR":
            # Require input_data for OCR
            if input_data is None:
                raise ValueError("OCR node requires input_data (list of image paths)")
            self.state = ocr_node({"images": input_data}, model, api_key=api_key)
            return self.state.get("markdown", "")
        elif node_name == "ExtractDiagnoses":
            self.state = extract_diagnoses_node(self.state, model, api_key=api_key)
            return self.state.get("diagnoses", {})
        elif node_name == "ExtractMedications":
            self.state = extract_medications_node(self.state, model, api_key=api_key)
            return self.state.get("medications", {})
        elif node_name == "FixMedications":
            self.state = fix_medications_node(self.state, model, api_key=api_key)
            return self.state.get("fixed_medications", {})
        elif node_name == "AddSummaryPills":
            self.state = add_summary_pills_node(self.state, model, api_key=api_key)
            return self.state.get("html_summary", "")
        else:
            raise ValueError(f"Unknown node: {node_name}")

# Create the global app_graph instance
app_graph = AppGraph()