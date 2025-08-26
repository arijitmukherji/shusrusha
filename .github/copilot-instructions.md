# GitHub Copilot Instructions for Shusrusha Medical Document Processor

## Project Overview

**Shusrusha** is a medical document processing application that converts discharge summary images into interactive HTML reports with medication links and analysis. The system uses OpenAI's GPT models for OCR, text extraction, and intelligent product matching through a multi-stage pipeline.

## Architecture

### Core Pipeline
The application follows a 5-stage processing pipeline:
1. **OCR** → Convert images to markdown text
2. **Extract Diagnoses** → Extract medical conditions and lab tests
3. **Extract Medications** → Extract medication names with instructions
4. **Fix Medications** → Match medications with PharmeEasy products using LLM
5. **Add Summary Pills** → Generate interactive HTML with medication pills

### Current Structure (Transitioning)
```
shusrusha/
├── langgraph_app.py          # Main application (monolithic - needs refactoring)
├── lib/
│   ├── __init__.py
│   └── graph_utils.py        # State management and OpenAI utilities
├── nodes/                    # [EMPTY] - Target for refactored nodes
├── discharge.ipynb           # Interactive testing notebook
├── requirements.txt          # Dependencies
└── images/                   # Test discharge summary images
```

## Key Technologies

- **LangGraph**: Workflow orchestration and state management
- **OpenAI API**: GPT-4 variants for OCR, extraction, and intelligent matching
- **PharmeEasy Integration**: Web scraping for Indian pharmaceutical data
- **Python Type System**: Comprehensive typing with TypedDict for state management

## Core Components

### State Management (`lib/graph_utils.py`)
```python
class GraphState(TypedDict):
    images: List[str]           # Input image paths
    markdown: str               # OCR output
    diagnoses: Dict[str, Any]   # Extracted medical conditions
    medications: Dict[str, Any] # Extracted medications
    fixed_medications: Dict[str, Any]  # Enhanced with PharmeEasy data
    html_summary: str           # Final interactive HTML
```

### OpenAI Model Handling
The `get_openai_params()` function handles different OpenAI model families:
- **GPT-4/3.5**: Standard parameters with `max_tokens`, `temperature`, `response_format`
- **GPT-5**: Uses `max_completion_tokens`, fixed `temperature=1`
- **o1/o3 models**: Limited parameters, no temperature or response_format

## Critical Patterns

### Node Function Signature
All processing nodes follow this pattern:
```python
def node_name(state: GraphState, model: str = "gpt-4o-mini") -> GraphState:
    """Process state and return updated state."""
    # Extract needed data from state
    # Call OpenAI API with get_openai_params()
    # Update state with results
    # Return updated state
```

### Error Handling Pattern
```python
try:
    # OpenAI API call with proper parameters
    api_params = get_openai_params(model, messages, max_tokens, use_json_format)
    response = client.chat.completions.create(**api_params)
    result = json.loads(response.choices[0].message.content)
except Exception as e:
    print(f"Error in {node_name}: {e}")
    # Provide fallback result
    result = default_value
```

### PharmeEasy Integration Pattern
1. **Fetch Content**: Use requests with proper headers and error handling
2. **Parse Products**: Use LLM to extract product listings from HTML
3. **Select Best Match**: Use specialized pharmacy-expert LLM prompts
4. **Generate URLs**: Ensure proper URL formatting and validation

## Current Issues & Refactoring Needed

### 🚨 Recent Fixes Applied
1. **Syntax Error Fixed**: Line 1006 conditional expression completed with `else ""`
2. **File Structure**: `lib/graph_utils.py` created with shared utilities
3. **Import Issues**: GraphState and get_openai_params properly separated

### 🎯 Current Status & Next Steps
The codebase is currently in a transitional state:
- ✅ Core functionality working in monolithic `langgraph_app.py`
- ✅ Shared utilities extracted to `lib/graph_utils.py`
- ❌ Individual node files not yet created (nodes/ directory empty)
- ❌ Duplicate code still exists between main file and lib

**Immediate Refactoring Tasks:**
1. Extract each node function to separate files in `nodes/`
2. Remove duplicate GraphState/get_openai_params from main file
3. Update imports to use modular structure
4. Test each extracted node individually

### 🎯 Refactoring Plan
Create modular structure:
```
nodes/
├── __init__.py
├── ocr_node.py              # Image to markdown conversion
├── extract_diagnoses_node.py # Medical condition extraction
├── extract_medications_node.py # Medication extraction
├── fix_medications_node.py  # PharmeEasy integration
└── add_summary_pills_node.py # HTML generation
```

## OpenAI Integration Guidelines

### Prompt Engineering Principles
1. **Medical Context**: Always specify "practicing in Kolkata, India" for local relevance
2. **Structured Output**: Use `response_format={"type": "json_object"}` when possible
3. **Domain Expertise**: Frame prompts with relevant medical/pharmacy expertise
4. **Error Recovery**: Provide fallback responses for failed API calls

### Model Selection Strategy
- **OCR**: `gpt-4o-mini` (cost-effective for vision tasks)
- **Extraction**: `gpt-4o-mini` (sufficient for structured extraction)
- **Product Matching**: `gpt-4o` (requires advanced reasoning)
- **HTML Generation**: `gpt-4o-mini` (template-based task)

## Web Scraping Guidelines

### PharmeEasy Integration
- Use proper User-Agent headers to avoid blocking
- Handle rate limiting and request timeouts
- Parse product listings with LLM for reliability
- Implement URL validation and cleanup

### Data Processing
- Limit content size for LLM processing (15KB chunks)
- Preserve product name and URL accuracy
- Handle relative URLs properly
- Implement confidence scoring for matches

## HTML Generation Patterns

### Interactive Elements
- **Medication Pills**: Subtle badges with hover tooltips
- **Confidence Indicators**: Visual scoring for match quality
- **List Structure**: Convert medications to semantic list items
- **Responsive Design**: Mobile-friendly layouts

### Styling Standards
- **Colors**: Green for exact matches, orange for alternatives, red for issues
- **Typography**: Clear hierarchies with proper spacing
- **Layout**: Grid-based responsive design
- **Accessibility**: Proper semantic HTML and alt text

## Testing & Development

### Notebook Workflow
Use `discharge.ipynb` for interactive development:
1. Load environment variables and modules
2. Test each node individually
3. Validate outputs with `display()` functions
4. Iterate on prompts and parameters

### Error Monitoring
- Print detailed status for each processing stage
- Log confidence scores and reasoning
- Track medication matching success rates
- Monitor API usage and costs

## Environment Setup

### Required Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Dependencies
Key packages from `requirements.txt`:
- `langgraph>=0.6.6` - Workflow orchestration
- `openai>=1.101.0` - API client
- `requests>=2.32.5` - HTTP client
- `beautifulsoup4>=4.13.5` - HTML parsing
- `python-dotenv>=1.1.1` - Environment management

## Code Quality Standards

### Type Safety
- Use `TypedDict` for all state objects
- Type annotate all function parameters and returns
- Leverage `Dict[str, Any]` for flexible JSON structures

### Documentation
- Include docstrings for all public functions
- Document complex business logic inline
- Maintain clear variable names reflecting medical context

### Error Handling
- Graceful degradation for API failures
- Meaningful error messages for debugging
- Fallback URLs and default values

## Common Patterns to Follow

### When Adding New Nodes
1. Create separate file in `nodes/` directory
2. Import `GraphState` from `lib.graph_utils`
3. Use standard node function signature
4. Include comprehensive error handling
5. Add debug print statements for monitoring

### When Modifying OpenAI Calls
1. Always use `get_openai_params()` utility
2. Test with multiple model types
3. Handle JSON parsing errors gracefully
4. Consider token limits and costs

### When Adding Features
1. Update `GraphState` if new data fields needed
2. Test with real medical documents
3. Validate HTML output across browsers
4. Consider mobile responsive design

## Medical Domain Considerations

### India-Specific Context
- Use Indian medical terminology and brand names
- Consider local availability of medications
- Respect cultural and linguistic variations
- Account for different prescription formats

### Privacy & Security
- Never log sensitive medical information
- Validate all external URLs
- Sanitize HTML output to prevent XSS
- Consider HIPAA-like compliance for medical data

## Future Enhancements

### Planned Features
- Support for multiple languages (Hindi, Bengali)
- Integration with additional pharmacy providers
- Batch processing for multiple documents
- API endpoint for external integrations

### Performance Optimizations
- Caching for repeated medication lookups
- Parallel processing for multiple medications
- Optimized image compression for OCR
- Rate limiting for external API calls

## Debugging & Troubleshooting

### Common Issues

#### Notebook Import Errors
- **Issue**: `SyntaxError` when importing `langgraph_app`
- **Solution**: Check for incomplete conditional expressions or missing `else` clauses
- **Debug**: Use `python -m py_compile langgraph_app.py` to validate syntax

#### OpenAI API Errors
- **Issue**: Model parameter mismatch (max_tokens vs max_completion_tokens)
- **Solution**: Always use `get_openai_params()` utility function
- **Debug**: Check model name prefix matching in parameter logic

#### PharmeEasy Scraping Failures
- **Issue**: Empty product lists or blocked requests
- **Solution**: Verify User-Agent headers and implement retry logic
- **Debug**: Print response status codes and content length

#### State Management Issues
- **Issue**: Missing data between pipeline stages
- **Solution**: Ensure proper state copying and field updates
- **Debug**: Print state keys at each node transition

### Monitoring & Logging

#### Production Monitoring
```python
# Add at start of each node
print(f"=== {node_name} Starting (Model: {model}) ===")
print(f"Input state keys: {list(state.keys())}")

# Add at end of each node  
print(f"=== {node_name} Complete ===")
print(f"Output state keys: {list(state.keys())}")
```

#### Performance Tracking
- Monitor OpenAI API usage and costs
- Track medication matching success rates
- Log processing times for each pipeline stage
- Monitor memory usage for large documents

---

*This documentation is specific to the Shusrusha medical document processing system. Always test changes with real medical documents and validate accuracy with medical professionals.*
