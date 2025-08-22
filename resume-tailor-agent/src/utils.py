"""
Utility functions for the Resume Tailor Agent.
"""

import os
import re
from typing import Optional, Dict, Any


def validate_file_path(file_path: str, extension: str = None) -> bool:
    """
    Validate if a file path exists and has the correct extension.
    
    Args:
        file_path (str): Path to the file
        extension (str, optional): Expected file extension (e.g., '.docx', '.txt')
    
    Returns:
        bool: True if file exists and has correct extension, False otherwise
    """
    if not os.path.exists(file_path):
        return False
    
    if extension and not file_path.lower().endswith(extension.lower()):
        return False
    
    return True


def clean_text(text: str) -> str:
    """
    Clean and normalize text by removing extra whitespace and special characters.
    
    Args:
        text (str): Input text to clean
    
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters that might interfere with processing
    text = re.sub(r'[^\w\s\-.,;:()\[\]{}\'\"@#$%&*+=<>?/\\|`~]', '', text)
    
    return text


def create_output_directory(output_path: str) -> bool:
    """
    Create output directory if it doesn't exist.
    
    Args:
        output_path (str): Path to the output file
    
    Returns:
        bool: True if directory exists or was created successfully, False otherwise
    """
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating output directory: {e}")
        return False


def read_text_file(file_path: str) -> Optional[str]:
    """
    Read content from a text file.
    
    Args:
        file_path (str): Path to the text file
    
    Returns:
        Optional[str]: File content or None if error occurred
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None


def extract_section_keywords() -> Dict[str, list]:
    """
    Return common keywords used to identify resume sections.
    
    Returns:
        Dict[str, list]: Dictionary mapping section names to their keywords
    """
    return {
        'summary': ['summary', 'profile', 'objective', 'about', 'overview'],
        'skills': ['skills', 'technical skills', 'core competencies', 'expertise', 'technologies'],
        'experience': ['experience', 'work experience', 'employment', 'professional experience', 'career history'],
        'education': ['education', 'academic background', 'qualifications'],
        'projects': ['projects', 'key projects', 'notable projects'],
        'certifications': ['certifications', 'certificates', 'credentials']
    }


def format_prompt_template() -> str:
    """
    Return a template for LLM prompts.
    
    Returns:
        str: Prompt template
    """
    return """
You are an expert resume writer. Your task is to tailor the following resume sections to match the provided job description.

JOB DESCRIPTION:
{job_description}

ORIGINAL RESUME SECTIONS:
{resume_sections}

INSTRUCTIONS:
1. Rewrite the SUMMARY section to highlight relevant experience and skills for this specific job
2. Update the SKILLS section to emphasize the most relevant technical and soft skills
3. Enhance the EXPERIENCE section by rewriting bullet points to better align with the job requirements
4. Maintain the original tone and style of the resume
5. Keep the same formatting structure
6. Do not add false information - only reframe existing content

Please provide the updated sections in the following format:

SUMMARY:
[Updated summary here]

SKILLS:
[Updated skills here]

EXPERIENCE:
[Updated experience here]
"""


def parse_llm_response(response: str) -> Dict[str, str]:
    """
    Parse the LLM response to extract updated resume sections.
    
    Args:
        response (str): Raw response from LLM
    
    Returns:
        Dict[str, str]: Dictionary with section names as keys and updated content as values
    """
    sections = {}
    
    # Define section patterns
    patterns = {
        'summary': r'SUMMARY:\s*(.*?)(?=SKILLS:|EXPERIENCE:|$)',
        'skills': r'SKILLS:\s*(.*?)(?=SUMMARY:|EXPERIENCE:|$)',
        'experience': r'EXPERIENCE:\s*(.*?)(?=SUMMARY:|SKILLS:|$)'
    }
    
    for section_name, pattern in patterns.items():
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            sections[section_name] = clean_text(content)
    
    return sections


def log_message(message: str, level: str = "INFO") -> None:
    """
    Simple logging function.
    
    Args:
        message (str): Message to log
        level (str): Log level (INFO, WARNING, ERROR)
    """
    print(f"[{level}] {message}")

