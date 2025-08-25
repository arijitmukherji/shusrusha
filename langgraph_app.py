from langgraph.graph import StateGraph
from typing import TypedDict, List, Dict, Any
import openai
import base64
import os
import requests
from urllib.parse import quote
import json

# Define the state structure
class GraphState(TypedDict):
    images: List[str]
    markdown: str
    diagnoses: Dict[str, Any]
    medications: Dict[str, Any]
    fixed_medications: Dict[str, Any]
    html_summary: str

def duckduckgo_search_results(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """
    Perform a DuckDuckGo search and return results as a list of dictionaries.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 10)
        
    Returns:
        List of dictionaries with 'title', 'url', 'snippet' keys
    """
    try:
        from ddgs import DDGS
        
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=max_results))
            
        # Format results
        formatted_results = []
        for result in raw_results:
            formatted_results.append({
                'title': result['title'],
                'url': result['href'],
                'snippet': result['body']
            })
            
        return formatted_results
        
    except ImportError:
        print("Error: ddgs package not installed.")
        return []
        
    except Exception as e:
        print(f"Search error: {str(e)}")
        return []

def duckduckgo_search(query: str, max_results: int = 10) -> None:
    """
    Perform a DuckDuckGo search for a given term and print the top results.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to display (default: 10)
    """
    try:
        from ddgs import DDGS
        
        print(f"Searching for: '{query}'")
        print("=" * 80)
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            
        if not results:
            print("No results found.")
            return
            
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   URL: {result['href']}")
            print(f"   Snippet: {result['body'][:200]}{'...' if len(result['body']) > 200 else ''}")
            print("-" * 80)
            
    except ImportError:
        print("Error: ddgs package not installed.")
        print("Please install it with: pip install ddgs")
        
    except Exception as e:
        print(f"Search error: {str(e)}")

def web_search_tool(query: str, site: str = None) -> str:
    """
    Perform a web search using a search API or web scraping.
    
    Args:
        query: Search query
        site: Optional site to search within (e.g., "1mg.com")
    
    Returns:
        Search results as a string
    """
    try:
        # Use DDGS search (no API key required)
        from ddgs import DDGS
        
        search_query = f"site:{site} {query}" if site else query
        
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=3))
            
        formatted_results = []
        for result in results:
            formatted_results.append(f"Title: {result['title']}\nURL: {result['href']}\nSnippet: {result['body']}\n")
        
        return "\n".join(formatted_results)
        
    except ImportError:
        # Fallback: construct search URLs manually
        encoded_query = quote(query)
        if site:
            search_urls = {
                "1mg.com": f"https://www.1mg.com",
                "pharmeasy.in": f"https://pharmeasy.in",
                "medindia.net": f"https://www.medindia.net",
                "mims.com": f"https://www.mims.com/india/"
            }
            return f"Search URL for {site}: {search_urls.get(site, f'https://www.google.com/search?q=site:{site}+{encoded_query}')}"
        else:
            return f"Search URL: https://www.google.com/search?q={encoded_query}"
    
    except Exception as e:
        return f"Search error: {str(e)}"

def get_openai_params(model: str, messages: list, max_tokens: int = 2048, temperature: float = 0.1, use_json_format: bool = True, tools: list = None) -> dict:
    """
    Get the correct OpenAI API parameters based on the model type.
    
    Args:
        model: The OpenAI model name
        messages: List of messages for the API call
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        use_json_format: Whether to use JSON response format
        tools: List of tools for function calling
    
    Returns:
        Dictionary of API parameters
    """
    base_params = {
        "model": model,
        "messages": messages
    }
    
    # Add tools if provided and model supports them
    if tools and not (model.startswith("o1") or model.startswith("o3")):
        base_params["tools"] = tools
        base_params["tool_choice"] = "auto"
    
    # Handle different model families
    if model.startswith("gpt-5") or model.startswith("o1") or model.startswith("o3"):
        # For GPT-5, o1, and o3 models, use max_completion_tokens
        base_params["max_completion_tokens"] = max_tokens
        
        # o1 and o3 models don't support response_format, temperature, or tools
        if model.startswith("o1") or model.startswith("o3"):
            # o1/o3 models: no temperature, no tools, no response_format
            if "tools" in base_params:
                base_params.pop("tools")
            if "tool_choice" in base_params:
                base_params.pop("tool_choice")
        elif model.startswith("gpt-5"):
            # GPT-5 models: only support temperature=1 (default), support tools and response_format
            base_params["temperature"] = 1  # Force temperature to 1 for GPT-5
            if use_json_format:
                base_params["response_format"] = {"type": "json_object"}
    else:
        # For GPT-4 and older models, use max_tokens
        base_params["max_tokens"] = max_tokens
        base_params["temperature"] = temperature  # Use custom temperature for older models
        if use_json_format and not tools:  # Don't use JSON format with tools
            base_params["response_format"] = {"type": "json_object"}
    
    return base_params

# Define web search tools for OpenAI function calling
web_search_tools = [
    {
        "type": "function",
        "function": {
            "name": "search_drug_database",
            "description": "Search Indian pharmaceutical databases for drug information",
            "parameters": {
                "type": "object",
                "properties": {
                    "drug_name": {
                        "type": "string",
                        "description": "The name of the drug to search for"
                    },
                    "site": {
                        "type": "string",
                        "enum": ["1mg.com", "pharmeasy.in", "medindia.net", "mims.com"],
                        "description": "Which Indian pharmacy site to search"
                    }
                },
                "required": ["drug_name", "site"]
            }
        }
    }
]

def handle_tool_calls(tool_calls):
    """Handle tool calls from OpenAI API response"""
    results = []
    for tool_call in tool_calls:
        if tool_call.function.name == "search_drug_database":
            args = json.loads(tool_call.function.arguments)
            search_result = web_search_tool(args["drug_name"], args["site"])
            results.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "content": search_result
            })
    return results

def fetch_url_content(url: str, timeout: int = 10) -> str:
    """
    Fetch the content of a URL and return the text.
    
    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds (default: 10)
    
    Returns:
        The text content of the webpage
    """
    try:
        from bs4 import BeautifulSoup
        
        # Set headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make the request
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up the text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit text length to avoid token limits
        max_length = 5000
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text
        
    except ImportError:
        return f"Error: BeautifulSoup not installed. Please install with: pip install beautifulsoup4"
    
    except requests.exceptions.RequestException as e:
        return f"Error fetching URL {url}: {str(e)}"
    
    except Exception as e:
        return f"Error processing content from {url}: {str(e)}"

def fetch_url_content_simple(url: str, timeout: int = 10) -> str:
    """
    Simple version that fetches raw HTML content with better error handling.
    
    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds (default: 10)
    
    Returns:
        The raw HTML content
    """
    try:
        # Better headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        print(f"Attempting to fetch: {url}")
        
        # Add session for better handling
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(url, timeout=timeout, allow_redirects=True)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '')
        print(f"Content type: {content_type}")
        
        # Get content
        content = response.text
        print(f"Content length: {len(content)} characters")
        
        # Limit content length
        max_length = 20000  # Increased limit
        if len(content) > max_length:
            content = content[:max_length] + "... [content truncated]"
            
        return content
        
    except requests.exceptions.Timeout:
        return f"Error: Timeout fetching {url} after {timeout} seconds"
    except requests.exceptions.ConnectionError:
        return f"Error: Connection failed for {url}"
    except requests.exceptions.HTTPError as e:
        return f"Error: HTTP {e.response.status_code} for {url}"
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"

def test_pharmeasy_fetch(medicine_name: str = "paracetamol"):
    """
    Test function to debug Pharmeasy fetching.
    """
    # Test different URL encoding approaches
    encoded_medicine = quote(medicine_name)
    url1 = f"https://pharmeasy.in/search/all?name={encoded_medicine}"
    
    print(f"Testing medicine: {medicine_name}")
    print(f"Encoded: {encoded_medicine}")
    print(f"URL: {url1}")
    print("=" * 80)
    
    # Try fetching
    content = fetch_url_content_simple(url1, timeout=15)
    
    if content.startswith("Error"):
        print("FAILED:")
        print(content)
    else:
        print("SUCCESS:")
        print(f"Content preview (first 500 chars):")
        print(content[:500])
        print("...")
        
        # Check if it looks like a valid page
        if "pharmeasy" in content.lower() and ("product" in content.lower() or "medicine" in content.lower()):
            print("✓ Content appears to be a valid Pharmeasy page")
        else:
            print("⚠ Content may not be a valid Pharmeasy page")
    
    return content

# Node functions
def ocr_node(state: GraphState, model: str = "gpt-4o-mini") -> GraphState:
    """
    images: list of file paths (jpg/png)
    Returns: markdown text (str)
    Uses GPT-4 Vision for OCR
    """
    # System prompt for OCR
    system_prompt = """Task. You are an expert medical assistant working in a hospital located 
    in Kolkata, India. Transcribe this discharge summary issued to a patient exactly 
    (i.e. preserve all sections/headers/order/wording). If in doubt about some unclear writing,
      try to match with terms that make sense in an India context, for medical field and 
      relevant diagnoses, and check medications against India availability. Then output a 
      simple markdown document with all the contents with the same content as the original"""
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Process images
    image_contents = []
    for image_path in state.get("images", []):
        try:
            # Read and encode image
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
                
            # Determine image type
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
            # Create messages for the API call
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please transcribe these medical discharge summary pages into markdown format."
                        }
                    ] + image_contents
                }
            ]
            
            # Get model-specific parameters
            api_params = get_openai_params(model, messages, max_tokens=4096, use_json_format=False)
            
            # Call OpenAI API with model-specific parameters
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
    Returns: structured JSON (diagnoses)
    Uses specified model for diagnosis extraction
    """
    # Get markdown from state
    markdown_text = state.get("markdown", "")
    
    # System prompt for diagnosis extraction
    system_prompt = """You are an expert medical doctor practising in Kolkata India. You have been given a hospital discharge report of a patient in simple mardown text format. Your job is to identify all the relevant medical terms in the document related to a) diagnosis names b) lab test names from the document. Ignore all medicine names. Keep in mind common terminology used in that part of the world. Return a JSON structure of the form
{"diagnoses": ["diagnosis term 1", "diagnosis term 2", ...], "lab_tests":["lab test name 1", "lab test name 2", ...]}"""
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    try:
        # Create messages for the API call
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"Please extract diagnoses and lab tests from this discharge summary:\n\n{markdown_text}"
            }
        ]
        
        # Get model-specific parameters
        api_params = get_openai_params(model, messages, max_tokens=2048, use_json_format=True)
        
        # Call OpenAI API with model-specific parameters
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
    Returns: structured JSON (medications)
    Uses specified model for medication extraction
    """
    # Get markdown from state
    markdown_text = state.get("markdown", "")
    
    # System prompt for medication extraction
    system_prompt = """You are an expert medical doctor practising in Kolkata India. You have been given a hospital discharge report of a patient in simple mardown text format. Your job is to identify all the relevant medication names from the document along with instructions. In case of difficulty identifying a medication name, make sure the names match actual medications used in that part of the world. Return a JSON structure of the form
{"medications": [{"name":"medicine_1", "instructions":"Twice daily", "duration":"continue"}, {"name":"medicine_2", "instructions":"as needed", "duration":"as needed"}, {"name":"medicine_3", "instructions":"BID", "duration":"10 days"}]}"""
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    try:
        # Create messages for the API call
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"Please extract medications with instructions and duration from this discharge summary:\n\n{markdown_text}"
            }
        ]
        
        # Get model-specific parameters
        api_params = get_openai_params(model, messages, max_tokens=2048, use_json_format=True)
        
        # Call OpenAI API with model-specific parameters
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

def fetch_pharmeasy_products_selenium(medicine_name: str, model: str = "gpt-4o-mini") -> List[Dict[str, str]]:
    """
    Fetch products from PharmeEasy using Selenium to handle JavaScript.
    
    Args:
        medicine_name: Name of the medicine to search for
        model: OpenAI model to use for parsing
    
    Returns:
        List of dictionaries with 'name' and 'url' keys for each product
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, WebDriverException
        import time
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        print(f"Setting up Selenium for: {medicine_name}")
        
        # Create driver
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # Construct URL and navigate
            encoded_medicine = quote(medicine_name)
            search_url = f"https://pharmeasy.in/search/all?name={encoded_medicine}"
            
            print(f"Navigating to: {search_url}")
            driver.get(search_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Try different selectors for product cards
            product_selectors = [
                "div[data-testid='product-card']",
                ".ProductCard_productCard__fGBQ_",
                "[class*='product-card']",
                "[class*='ProductCard']",
                ".product-item",
                ".medicine-card"
            ]
            
            products_found = False
            for selector in product_selectors:
                try:
                    print(f"Trying selector: {selector}")
                    wait = WebDriverWait(driver, 5)
                    elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
                    if elements:
                        print(f"Found {len(elements)} elements with selector: {selector}")
                        products_found = True
                        break
                except TimeoutException:
                    continue
            
            if not products_found:
                print("No product elements found, getting full page source")
            
            # Get page source after JavaScript execution
            page_source = driver.page_source
            print(f"Page source length: {len(page_source)} characters")
            
            # Check if we got a valid page
            if "pharmeasy" not in page_source.lower():
                print("Warning: Page doesn't appear to be Pharmeasy")
            
            # Parse with LLM
            return parse_pharmeasy_products_with_llm_selenium(page_source, model)
            
        finally:
            driver.quit()
            
    except ImportError:
        print("Selenium not installed. Install with: pip install selenium")
        print("Also install ChromeDriver: brew install chromedriver (on Mac)")
        return []
    except WebDriverException as e:
        print(f"WebDriver error: {e}")
        print("Make sure ChromeDriver is installed and in PATH")
        return []
    except Exception as e:
        print(f"Error with Selenium fetch: {e}")
        return []

def parse_pharmeasy_products_with_llm_selenium(html_content: str, model: str = "gpt-4o-mini") -> List[Dict[str, str]]:
    """
    Use LLM to parse PharmeEasy HTML content rendered by Selenium.
    """
    try:
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Enhanced system prompt for Selenium-rendered content
        system_prompt = """You are an expert web scraper. Your job is to parse HTML content from PharmeEasy.in search results that has been rendered by JavaScript.

From the HTML content, find product listings/cards and extract up to 10 products. Look for:
- Product names/titles (could be in various tags like h3, h4, div with product names)
- Product URLs/links (look for href attributes pointing to product pages)
- Price information if available

Common Pharmeasy patterns to look for:
- div elements with classes containing "product", "card", "medicine"
- Links (a tags) with href containing "/online-medicine-order/" or "/medicines/"
- Product names often in h3, h4, or span elements

Return a JSON structure with the format:
{"products": [{"name": "Product Name 1", "url": "https://pharmeasy.in/online-medicine-order/..."}, {"name": "Product Name 2", "url": "https://pharmeasy.in/..."}, ...]}

If URLs are relative (starting with /), prepend "https://pharmeasy.in". If you cannot find 10 products, return as many as you can find. If no products are found, return an empty products array."""
        
        # Truncate HTML content to avoid token limits
        max_html_length = 20000  # Increased for Selenium content
        if len(html_content) > max_html_length:
            # Try to keep the middle part which likely has products
            start_chunk = html_content[:5000]
            end_chunk = html_content[-5000:]
            middle_start = len(html_content) // 3
            middle_chunk = html_content[middle_start:middle_start + 10000]
            html_content = start_chunk + "\n... [content truncated] ...\n" + middle_chunk + "\n... [content truncated] ...\n" + end_chunk
        
        # Create messages for the API call
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"Please parse this PharmeEasy HTML content (rendered by Selenium) and extract the products:\n\n{html_content}"
            }
        ]
        
        # Get model-specific parameters
        api_params = get_openai_params(model, messages, max_tokens=2048, use_json_format=True)
        
        # Call OpenAI API
        response = client.chat.completions.create(**api_params)
        
        parsed_result = json.loads(response.choices[0].message.content)
        
        # Extract products list
        products = parsed_result.get("products", [])
        
        # Clean up URLs
        cleaned_products = []
        for product in products:
            url = product.get("url", "")
            if url.startswith("/"):
                url = "https://pharmeasy.in" + url
            elif not url.startswith("http"):
                url = "https://pharmeasy.in/" + url
            
            cleaned_products.append({
                "name": product.get("name", ""),
                "url": url
            })
        
        print(f"Extracted {len(cleaned_products)} products from Selenium-rendered HTML")
        return cleaned_products
        
    except Exception as e:
        print(f"Error parsing Pharmeasy HTML with LLM: {e}")
        return []

def fix_medications_node(state: GraphState, model: str = "gpt-4o-mini") -> GraphState:
    """
    Returns: fixed medications JSON
    Uses Selenium to fetch PharmeEasy content for each medication and extracts products
    """
    # Get medications and diagnoses from state
    medications_data = state.get("medications", {"medications": []})
    diagnoses_data = state.get("diagnoses", {"diagnoses": [], "lab_tests": []})
    
    # Process each medication individually
    fixed_medications_list = []
    
    for i, medication in enumerate(medications_data.get("medications", [])):
        medicine_name = medication.get('name', 'Unknown')
        print(f"\n--- Processing medication {i+1}: {medicine_name} ---")
        
        try:
            # Fetch Pharmeasy products using Selenium
            products = fetch_pharmeasy_products_selenium(medicine_name, model)
            
            # Create the enhanced medication object
            medication_copy = medication.copy()
            
            if products:
                # Use the first product as the primary match
                primary_product = products[0]
                medication_copy.update({
                    "url": primary_product["url"],
                    "pharmeasy_name": primary_product["name"],
                    "all_products": products[:10]  # Store all found products
                })
                
                # Check if the primary product name differs significantly from original
                original_name_lower = medicine_name.lower()
                pharmeasy_name_lower = primary_product["name"].lower()
                
                if original_name_lower not in pharmeasy_name_lower and pharmeasy_name_lower not in original_name_lower:
                    medication_copy["modified_name"] = primary_product["name"]
                    medication_copy["reason"] = f"Best match found on PharmeEasy: {primary_product['name']}"
                
                print(f"✓ Found {len(products)} products. Primary match: {primary_product['name']}")
            else:
                # No products found, use fallback
                fallback_url = f"https://pharmeasy.in/search/all?name={medicine_name.replace(' ', '%20')}"
                medication_copy.update({
                    "url": fallback_url,
                    "reason": "No specific products found on PharmeEasy, providing search URL",
                    "all_products": []
                })
                print(f"✗ No products found for {medicine_name}, using fallback URL")
            
            fixed_medications_list.append(medication_copy)
                
        except Exception as e:
            print(f"✗ Error processing medication {medicine_name}: {e}")
            # Fallback for this medication
            medication_copy = medication.copy()
            fallback_url = f"https://pharmeasy.in/search/all?name={medicine_name.replace(' ', '%20')}"
            medication_copy.update({
                "url": fallback_url,
                "reason": f"Error during processing: {str(e)}",
                "all_products": []
            })
            fixed_medications_list.append(medication_copy)
    
    # Create final result
    fixed_medications_json = {"medications": fixed_medications_list}
    
    # Print the fixed medications output
    print(f"\n=== Fix Medications Node Output (Model: {model}) ===")
    print(f"Processed {len(fixed_medications_list)} medications using Selenium")
    for med in fixed_medications_list:
        product_count = len(med.get('all_products', []))
        status = "✓" if product_count > 0 else "✗"
        print(f"{status} {med.get('name', 'Unknown')}: {product_count} products found")
    print("==================================================")
    
    state["fixed_medications"] = fixed_medications_json
    return state

def add_summary_pills_node(state: GraphState, model: str = "gpt-4o-mini") -> GraphState:
    """
    Generate HTML summary with pill-style medication display.
    """
    print(f"=== Add Summary Pills Node (Model: {model}) ===")
    
    # Get data from state
    diagnoses = state.get("diagnoses", {})
    medications = state.get("medications", {})
    fixed_medications = state.get("fixed_medications", {})
    
    # Generate a simple HTML summary
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Medical Summary</title>
        <style>
            .pill {{ background: #e3f2fd; padding: 8px 16px; margin: 4px; border-radius: 20px; display: inline-block; }}
            .diagnosis {{ background: #ffebee; }}
            .medication {{ background: #e8f5e8; }}
        </style>
    </head>
    <body>
        <h1>Medical Summary</h1>
        
        <h2>Diagnoses</h2>
        <div>
        {"".join([f'<span class="pill diagnosis">{d}</span>' for d in diagnoses.get("diagnoses", [])])}
        </div>
        
        <h2>Medications</h2>
        <div>
        {"".join([f'<span class="pill medication"><a href="{m.get("url", "")}" target="_blank">{m.get("name", "")}</a></span>' for m in fixed_medications.get("medications", [])])}
        </div>
        
        <p>Generated with {model}</p>
    </body>
    </html>
    """
    
    print("HTML summary generated")
    print("=======================================")
    
    state["html_summary"] = html_content
    return state

# Create the LangGraph workflow
def create_app_graph():
    """Create and return the LangGraph workflow."""
    
    # Create the graph
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("OCR", ocr_node)
    workflow.add_node("ExtractDiagnoses", extract_diagnoses_node)
    workflow.add_node("ExtractMedications", extract_medications_node)
    workflow.add_node("FixMedications", fix_medications_node)
    workflow.add_node("AddSummaryPills", add_summary_pills_node)
    
    # Set entry point
    workflow.set_entry_point("OCR")
    
    # Add edges (workflow connections)
    workflow.add_edge("OCR", "ExtractDiagnoses")
    workflow.add_edge("ExtractDiagnoses", "ExtractMedications")
    workflow.add_edge("ExtractMedications", "FixMedications")
    workflow.add_edge("FixMedications", "AddSummaryPills")
    
    # Compile the graph
    return workflow.compile()

class AppGraph:
    """Wrapper class for the LangGraph workflow with convenience methods."""
    
    def __init__(self):
        self.graph = create_app_graph()
        self.state = {}
    
    def run_node(self, node_name: str, input_data=None, model: str = "gpt-4o-mini"):
        """
        Run a specific node in the workflow.
        
        Args:
            node_name: Name of the node to run
            input_data: Input data for the node
            model: Model to use for the node
            
        Returns:
            Output from the node
        """
        print(f"Running node: {node_name} with model: {model}")
        
        # Handle different input types
        if node_name == "OCR" and input_data:
            self.state["images"] = input_data
        
        # Run the specific node function
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

# Add helper functions as attributes for compatibility
app_graph.fetch_url_content = fetch_url_content
app_graph.fetch_url_content_simple = fetch_url_content_simple
app_graph.duckduckgo_search_results = duckduckgo_search_results
app_graph.duckduckgo_search = duckduckgo_search
app_graph.test_pharmeasy_fetch = test_pharmeasy_fetch
app_graph.fetch_pharmeasy_products_selenium = fetch_pharmeasy_products_selenium
app_graph.web_search_tool = web_search_tool

# For debugging - make state accessible
current_state = app_graph.state