from langgraph.graph import StateGraph
from typing import TypedDict, List, Dict, Any
import openai
import base64
import os

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
    
    Args:
        model: The OpenAI model name
        messages: List of messages for the API call
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        use_json_format: Whether to use JSON response format
    
    Returns:
        Dictionary of API parameters
    """
    base_params = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }
    
    # Handle different model families
    if model.startswith("gpt-5") or model.startswith("o1"):
        # For GPT-5 and o1 models, use max_completion_tokens
        base_params["max_completion_tokens"] = max_tokens
        
        # o1 models don't support response_format or temperature
        if model.startswith("o1"):
            base_params.pop("temperature")  # Remove temperature for o1 models
        elif use_json_format:
            base_params["response_format"] = {"type": "json_object"}
    else:
        # For GPT-4 and older models, use max_tokens
        base_params["max_tokens"] = max_tokens
        if use_json_format:
            base_params["response_format"] = {"type": "json_object"}
    
    return base_params

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
        
        import json
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
        
        import json
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

def fix_medications_node(state: GraphState, model: str = "gpt-4o-mini") -> GraphState:
    """
    Returns: fixed medications JSON
    Uses browser tool calling for Google India
    """
    print(f"=== Fix Medications Node (Model: {model}) ===")
    # TODO: Implement browser tool logic for Google India using get_openai_params()
    fixed_medications_json = {"fixed_medications": []}
    print(f"Placeholder: Would use {model} for medication fixing")
    print("=======================================")
    
    state["fixed_medications"] = fixed_medications_json
    return state

def add_summary_pills_node(state: GraphState, model: str = "gpt-4o-mini") -> GraphState:
    """
    Returns: self-contained HTML file (str)
    """
    print(f"=== Add Summary Pills Node (Model: {model}) ===")
    # TODO: Implement HTML generation logic using get_openai_params()
    html_content = f"<html><body><h1>Summary Pills</h1><p>Generated with {model}</p></body></html>"
    print(f"Placeholder: Would use {model} for HTML generation")
    print("=========================================")
    
    state["html_summary"] = html_content
    return state

# Graph definition
workflow = StateGraph(GraphState)

# Add nodes
workflow.add_node("OCR", ocr_node)
workflow.add_node("ExtractDiagnoses", extract_diagnoses_node)
workflow.add_node("ExtractMedications", extract_medications_node)
workflow.add_node("FixMedications", fix_medications_node)
workflow.add_node("AddSummaryPills", add_summary_pills_node)

# Add edges
workflow.set_entry_point("OCR")
workflow.add_edge("OCR", "ExtractDiagnoses")
workflow.add_edge("ExtractDiagnoses", "ExtractMedications")
workflow.add_edge("ExtractMedications", "FixMedications")
workflow.add_edge("FixMedications", "AddSummaryPills")

# Compile the graph
app_graph = workflow.compile()

# Simple state management for individual node execution
current_state = {}

# Helper function for running individual nodes (for compatibility)
def run_node(node_name: str, *args, model: str = "gpt-4o-mini"):
    print(f"Running node: {node_name} with model: {model}")
    if node_name == "OCR":
        current_state.clear()
        current_state["images"] = args[0]
        result = ocr_node(current_state, model=model)
        return result["markdown"]
    elif node_name == "ExtractDiagnoses":
        result = extract_diagnoses_node(current_state, model=model)
        return result["diagnoses"]
    elif node_name == "ExtractMedications":
        result = extract_medications_node(current_state, model=model)
        return result["medications"]
    elif node_name == "FixMedications":
        result = fix_medications_node(current_state, model=model)
        return result["fixed_medications"]
    elif node_name == "AddSummaryPills":
        result = add_summary_pills_node(current_state, model=model)
        return result["html_summary"]

# Add run_node method to app_graph for compatibility
app_graph.run_node = run_node

# Example usage
if __name__ == "__main__":
    images = ["scan1.jpg", "scan2.png"]
    initial_state = {"images": images}
    final_result = app_graph.invoke(initial_state)
    print(final_result["html_summary"])
