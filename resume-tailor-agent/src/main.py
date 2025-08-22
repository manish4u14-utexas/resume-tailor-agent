#!/usr/bin/env python3
"""
Resume Tailor Agent - Main CLI Interface

This script provides the main command-line interface for the Resume Tailor Agent.
It orchestrates the entire process of tailoring resumes to job descriptions using LLMs.
"""

import argparse
import sys
import os
from typing import Optional, Dict, Any

# Add the src directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from resume_parser import ResumeParser
from llm_interface import LLMInterface
from utils import (
    validate_file_path, 
    read_text_file, 
    create_output_directory, 
    format_prompt_template,
    parse_llm_response,
    log_message
)


class ResumeTailorAgent:
    """
    Main class for the Resume Tailor Agent application.
    """
    
    def __init__(self):
        """Initialize the Resume Tailor Agent."""
        self.llm_interface = LLMInterface()
        self.resume_parser = None
        
    def validate_inputs(self, resume_path: str, jd_path: str, output_path: str) -> bool:
        """
        Validate all input parameters.
        
        Args:
            resume_path (str): Path to the resume file
            jd_path (str): Path to the job description file
            output_path (str): Path for the output file
        
        Returns:
            bool: True if all inputs are valid, False otherwise
        """
        # Validate resume file
        if not validate_file_path(resume_path, '.docx'):
            log_message(f"Resume file not found or invalid: {resume_path}", "ERROR")
            return False
        
        # Validate job description file
        if not validate_file_path(jd_path, '.txt'):
            log_message(f"Job description file not found or invalid: {jd_path}", "ERROR")
            return False
        
        # Validate output directory
        if not create_output_directory(output_path):
            log_message(f"Cannot create output directory for: {output_path}", "ERROR")
            return False
        
        return True
    
    def load_job_description(self, jd_path: str) -> Optional[str]:
        """
        Load job description from file.
        
        Args:
            jd_path (str): Path to the job description file
        
        Returns:
            Optional[str]: Job description content or None if failed
        """
        jd_content = read_text_file(jd_path)
        if not jd_content:
            log_message("Failed to read job description file", "ERROR")
            return None
        
        log_message(f"Loaded job description ({len(jd_content)} characters)")
        return jd_content.strip()
    
    def extract_resume_sections(self, resume_path: str) -> Optional[Dict[str, str]]:
        """
        Extract sections from the resume.
        
        Args:
            resume_path (str): Path to the resume file
        
        Returns:
            Optional[Dict[str, str]]: Extracted sections or None if failed
        """
        self.resume_parser = ResumeParser(resume_path)
        
        if not self.resume_parser.load_document():
            log_message("Failed to load resume document", "ERROR")
            return None
        
        sections = self.resume_parser.extract_sections()
        
        # Filter out empty sections
        non_empty_sections = {k: v for k, v in sections.items() if v.strip()}
        
        if not non_empty_sections:
            log_message("No content sections found in resume", "ERROR")
            return None
        
        log_message(f"Extracted {len(non_empty_sections)} sections from resume")
        return non_empty_sections
    
    def build_tailoring_prompt(self, resume_sections: Dict[str, str], job_description: str) -> str:
        """
        Build the prompt for LLM to tailor the resume.
        
        Args:
            resume_sections (Dict[str, str]): Extracted resume sections
            job_description (str): Job description content
        
        Returns:
            str: Formatted prompt for the LLM
        """
        # Format resume sections for the prompt
        sections_text = ""
        for section_name, content in resume_sections.items():
            if content.strip():
                sections_text += f"\n{section_name.upper()}:\n{content}\n"
        
        # Use the template from utils
        template = format_prompt_template()
        
        prompt = template.format(
            job_description=job_description,
            resume_sections=sections_text
        )
        
        log_message(f"Built tailoring prompt ({len(prompt)} characters)")
        return prompt
    
    def tailor_resume_with_llm(self, prompt: str, model: str) -> Optional[Dict[str, str]]:
        """
        Use LLM to tailor the resume sections.
        
        Args:
            prompt (str): The tailoring prompt
            model (str): LLM model to use
        
        Returns:
            Optional[Dict[str, str]]: Tailored sections or None if failed
        """
        log_message(f"Sending prompt to LLM (model: {model})")
        
        response = self.llm_interface.run_llm(prompt, model)
        
        if not response:
            log_message("No response received from LLM", "ERROR")
            return None
        
        log_message(f"Received LLM response ({len(response)} characters)")
        
        # Parse the LLM response to extract sections
        tailored_sections = parse_llm_response(response)
        
        if not tailored_sections:
            log_message("Could not parse sections from LLM response", "ERROR")
            log_message(f"Raw response: {response[:500]}...", "WARNING")
            return None
        
        log_message(f"Parsed {len(tailored_sections)} tailored sections")
        return tailored_sections
    
    def update_and_save_resume(self, tailored_sections: Dict[str, str], output_path: str) -> bool:
        """
        Update the resume with tailored content and save it.
        
        Args:
            tailored_sections (Dict[str, str]): Tailored sections from LLM
            output_path (str): Path to save the updated resume
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.resume_parser:
            log_message("Resume parser not initialized", "ERROR")
            return False
        
        # Update the resume sections
        if not self.resume_parser.update_sections(tailored_sections):
            log_message("Failed to update resume sections", "ERROR")
            return False
        
        # Save the updated resume
        if not self.resume_parser.save_document(output_path):
            log_message("Failed to save updated resume", "ERROR")
            return False
        
        log_message(f"Successfully saved tailored resume to: {output_path}")
        return True
    
    def run(self, resume_path: str, jd_path: str, output_path: str, model: str = "local") -> bool:
        """
        Run the complete resume tailoring process.
        
        Args:
            resume_path (str): Path to the resume file
            jd_path (str): Path to the job description file
            output_path (str): Path for the output file
            model (str): LLM model to use
        
        Returns:
            bool: True if successful, False otherwise
        """
        log_message("Starting Resume Tailor Agent")
        log_message(f"Resume: {resume_path}")
        log_message(f"Job Description: {jd_path}")
        log_message(f"Output: {output_path}")
        log_message(f"Model: {model}")
        
        # Step 1: Validate inputs
        if not self.validate_inputs(resume_path, jd_path, output_path):
            return False
        
        # Step 2: Load job description
        job_description = self.load_job_description(jd_path)
        if not job_description:
            return False
        
        # Step 3: Extract resume sections
        resume_sections = self.extract_resume_sections(resume_path)
        if not resume_sections:
            return False
        
        # Step 4: Build tailoring prompt
        prompt = self.build_tailoring_prompt(resume_sections, job_description)
        
        # Step 5: Get tailored content from LLM
        tailored_sections = self.tailor_resume_with_llm(prompt, model)
        if not tailored_sections:
            return False
        
        # Step 6: Update and save resume
        if not self.update_and_save_resume(tailored_sections, output_path):
            return False
        
        log_message("Resume tailoring completed successfully! 🎉")
        return True


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Resume Tailor Agent - Tailor your resume to specific job descriptions using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --resume data/resume.docx --jd data/job.txt --out output/tailored_resume.docx
  %(prog)s --resume data/resume.docx --jd data/job.txt --out output/tailored_resume.docx --model openai
  %(prog)s --resume data/resume.docx --jd-text "Software Engineer position..." --out output/tailored_resume.docx

Supported models:
  local      - Use local Ollama (default: mistral)
  openai     - Use OpenAI GPT models (requires OPENAI_API_KEY)
  anthropic  - Use Anthropic Claude models (requires ANTHROPIC_API_KEY)
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--resume', '-r',
        required=True,
        help='Path to the resume file (.docx format)'
    )
    
    parser.add_argument(
        '--out', '-o',
        required=True,
        help='Path for the output tailored resume (.docx format)'
    )
    
    # Job description input (mutually exclusive)
    jd_group = parser.add_mutually_exclusive_group(required=True)
    jd_group.add_argument(
        '--jd', '-j',
        help='Path to the job description file (.txt format)'
    )
    jd_group.add_argument(
        '--jd-text',
        help='Job description as a text string'
    )
    
    # Optional arguments
    parser.add_argument(
        '--model', '-m',
        default='local',
        choices=['local', 'openai', 'anthropic'],
        help='LLM model to use (default: local)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--test-llm',
        action='store_true',
        help='Test LLM connection and exit'
    )
    
    return parser


def handle_jd_text_input(jd_text: str) -> str:
    """
    Handle job description provided as text input.
    
    Args:
        jd_text (str): Job description text
    
    Returns:
        str: Path to temporary file containing the job description
    """
    import tempfile
    
    # Create a temporary file for the job description
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    temp_file.write(jd_text)
    temp_file.close()
    
    log_message(f"Created temporary job description file: {temp_file.name}")
    return temp_file.name


def test_llm_connection(model: str) -> bool:
    """
    Test LLM connection.
    
    Args:
        model (str): Model to test
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    log_message(f"Testing connection to {model} model...")
    
    interface = LLMInterface()
    available_models = interface.get_available_models()
    
    log_message(f"Available models: {available_models}")
    
    if model in available_models and available_models[model]:
        success = interface.test_connection(model)
        if success:
            log_message(f"✓ {model} connection successful")
            return True
        else:
            log_message(f"✗ {model} connection failed")
            return False
    else:
        log_message(f"✗ {model} not available or not configured")
        return False


def main():
    """Main entry point for the application."""
    parser = create_argument_parser()
    
    # Handle test mode first (before parsing all args)
    if '--test-llm' in sys.argv:
        # Create a minimal parser for test mode
        test_parser = argparse.ArgumentParser()
        test_parser.add_argument('--test-llm', action='store_true')
        test_parser.add_argument('--model', default='local', choices=['local', 'openai', 'anthropic'])
        test_args, _ = test_parser.parse_known_args()
        
        success = test_llm_connection(test_args.model)
        sys.exit(0 if success else 1)
    
    # Parse all arguments normally
    args = parser.parse_args()
    
    # Handle job description text input
    jd_path = args.jd
    temp_jd_file = None
    
    if args.jd_text:
        temp_jd_file = handle_jd_text_input(args.jd_text)
        jd_path = temp_jd_file
    
    try:
        # Create and run the agent
        agent = ResumeTailorAgent()
        success = agent.run(
            resume_path=args.resume,
            jd_path=jd_path,
            output_path=args.out,
            model=args.model
        )
        
        if success:
            print(f"\n🎉 Success! Tailored resume saved to: {args.out}")
            sys.exit(0)
        else:
            print("\n❌ Resume tailoring failed. Check the logs above for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        log_message(f"Unexpected error: {e}", "ERROR")
        sys.exit(1)
    finally:
        # Clean up temporary file if created
        if temp_jd_file and os.path.exists(temp_jd_file):
            os.unlink(temp_jd_file)
            log_message(f"Cleaned up temporary file: {temp_jd_file}")


if __name__ == "__main__":
    main()

