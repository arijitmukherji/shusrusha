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

# Node functions
def ocr_node(state: GraphState) -> GraphState:
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
    for image_path in state["images"]:
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
            
            # Call GPT-4o API
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=4096,
                temperature=0.1
            )
            
            markdown_text = response.choices[0].message.content
            
        except Exception as e:
            print(f"Error processing images with OpenAI API: {e}")
            markdown_text = f"# OCR Error\nFailed to process images: {str(e)}"
    
    # Print the markdown text
    print("=== OCR Node Output ===")
    print(markdown_text)
    print("======================")
    
    state["markdown"] = markdown_text
    return state

def extract_diagnoses_node(state: GraphState) -> GraphState:
    """
    markdown_text: str
    Returns: structured JSON (diagnoses)
    Uses GPT-5 mini (no reasoning)
    """
    # TODO: Implement GPT-5 mini extraction logic
    diagnoses_json = {"diagnoses": []}
    state["diagnoses"] = diagnoses_json
    return state

def extract_medications_node(state: GraphState) -> GraphState:
    """
    markdown_text: str
    diagnoses_json: dict
    Returns: structured JSON (medications)
    """
    # TODO: Implement medication extraction logic
    medications_json = {"medications": []}
    state["medications"] = medications_json
    return state

def fix_medications_node(state: GraphState) -> GraphState:
    """
    markdown_text: str
    diagnoses_json: dict
    medications_json: dict
    Returns: fixed medications JSON
    Uses browser tool calling for Google India
    """
    # TODO: Implement browser tool logic for Google India
    fixed_medications_json = {"fixed_medications": []}
    state["fixed_medications"] = fixed_medications_json
    return state

def add_summary_pills_node(state: GraphState) -> GraphState:
    """
    markdown_text: str
    diagnoses_json: dict
    fixed_medications_json: dict
    Returns: self-contained HTML file (str)
    """
    # TODO: Implement HTML generation logic
    html_content = "<html><body><h1>Summary Pills</h1></body></html>"
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

# Helper function for running individual nodes (for compatibility)
def run_node(node_name: str, *args):
    print("Running node:", node_name)
    if node_name == "OCR":
        initial_state = {"images": args[0]}
        result = app_graph.invoke(initial_state)
        print("OCR", initial_state, result)
        return result["markdown"]
    elif node_name == "ExtractDiagnoses":
        initial_state = {"markdown": args[0]}
        result = app_graph.invoke(initial_state)
        return result["diagnoses"]
    elif node_name == "ExtractMedications":
        initial_state = {"markdown": args[0], "diagnoses": args[1]}
        result = app_graph.invoke(initial_state)
        return result["medications"]
    elif node_name == "FixMedications":
        initial_state = {"markdown": args[0], "diagnoses": args[1], "medications": args[2]}
        result = app_graph.invoke(initial_state)
        return result["fixed_medications"]
    elif node_name == "AddSummaryPills":
        initial_state = {"markdown": args[0], "diagnoses": args[1], "fixed_medications": args[2]}
        result = app_graph.invoke(initial_state)
        return result["html_summary"]

# Add run_node method to app_graph for compatibility
app_graph.run_node = run_node

# Example usage
if __name__ == "__main__":
    images = ["scan1.jpg", "scan2.png"]
    initial_state = {"images": images}
    final_result = app_graph.invoke(initial_state)
    print(final_result["html_summary"])
