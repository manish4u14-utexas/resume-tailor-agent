"""
LLM Interface for Resume Tailor Agent.
Provides a unified interface for interacting with different LLM providers.
"""

import os
import json
import time
from typing import Optional, Dict, Any
import requests
from utils import log_message

# Import API clients
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    log_message("OpenAI library not available", "WARNING")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    log_message("Anthropic library not available", "WARNING")


class LLMInterface:
    """
    Unified interface for interacting with different LLM providers.
    """
    
    def __init__(self):
        """Initialize the LLM interface."""
        self.supported_models = {
            'local': ['phi3:mini', 'mistral', 'llama2', 'codellama', 'neural-chat'],
            'openai': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo-preview'],
            'anthropic': ['claude-3-sonnet-20240229', 'claude-3-haiku-20240307', 'claude-3-opus-20240229'],
            'groq': ['llama3-8b-8192', 'llama3-70b-8192', 'mixtral-8x7b-32768']
        }
        
        # Initialize API clients
        self.openai_client = None
        self.anthropic_client = None
        self.groq_client = None
        
        self._setup_api_clients()
    
    def _setup_api_clients(self):
        """Setup API clients for different providers."""
        # Setup OpenAI client
        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                try:
                    # Try to create OpenAI client with minimal configuration
                    self.openai_client = openai.OpenAI(
                        api_key=api_key,
                        timeout=60.0
                    )
                    log_message("OpenAI client initialized successfully")
                except Exception as e:
                    log_message(f"Failed to initialize OpenAI client: {e}", "ERROR")
                    # Set a flag to indicate OpenAI is available but client failed
                    self.openai_client = "failed"
            else:
                log_message("OPENAI_API_KEY not found in environment variables", "WARNING")
        
        # Setup Anthropic client
        if ANTHROPIC_AVAILABLE:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                try:
                    self.anthropic_client = anthropic.Anthropic(api_key=api_key)
                    log_message("Anthropic client initialized successfully")
                except Exception as e:
                    log_message(f"Failed to initialize Anthropic client: {e}", "ERROR")
            else:
                log_message("ANTHROPIC_API_KEY not found in environment variables", "WARNING")
        
        # Setup Groq client
        groq_api_key = os.getenv('GROQ_API_KEY')
        if groq_api_key:
            try:
                # Use OpenAI client for Groq (compatible API)
                if OPENAI_AVAILABLE:
                    self.groq_client = openai.OpenAI(
                        api_key=groq_api_key,
                        base_url="https://api.groq.com/openai/v1",
                        timeout=60.0
                    )
                    log_message("Groq client initialized successfully")
            except Exception as e:
                log_message(f"Failed to initialize Groq client: {e}", "ERROR")
        else:
            log_message("GROQ_API_KEY not found in environment variables", "WARNING")
    
    def run_llm(self, prompt: str, model: str = "local", max_retries: int = 3) -> Optional[str]:
        """
        Run LLM inference with the specified model.
        
        Args:
            prompt (str): The prompt to send to the LLM
            model (str): Model identifier (e.g., 'local', 'openai', 'anthropic')
            max_retries (int): Maximum number of retry attempts
        
        Returns:
            Optional[str]: LLM response or None if failed
        """
        log_message(f"Running LLM inference with model: {model}")
        
        for attempt in range(max_retries):
            try:
                if model == "local" or model.startswith("ollama"):
                    return self._run_ollama(prompt, model)
                elif model == "openai" or model.startswith("gpt"):
                    return self._run_openai(prompt, model)
                elif model == "anthropic" or model.startswith("claude"):
                    return self._run_anthropic(prompt, model)
                elif model == "groq" or model.startswith("llama3") or model.startswith("mixtral"):
                    return self._run_groq(prompt, model)
                else:
                    log_message(f"Unsupported model: {model}", "ERROR")
                    return None
                    
            except Exception as e:
                log_message(f"Attempt {attempt + 1} failed: {e}", "WARNING")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    log_message(f"All {max_retries} attempts failed", "ERROR")
                    return None
        
        return None
    
    def _run_ollama(self, prompt: str, model: str = "local") -> Optional[str]:
        """
        Run inference using local Ollama.
        
        Args:
            prompt (str): The prompt to send
            model (str): Model identifier
        
        Returns:
            Optional[str]: Response from Ollama or None if failed
        """
        # Default to phi3:mini if just "local" is specified
        ollama_model = "phi3:mini" if model == "local" else model.replace("ollama:", "")
        
        ollama_url = "http://localhost:11434/api/generate"
        
        payload = {
            "model": ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower for more focused, structured output
                "top_p": 0.8,
                "num_predict": 2000,  # Use num_predict instead of max_tokens for Ollama
                "repeat_penalty": 1.1,  # Reduce repetition
                "stop": ["\n\n\n"]  # Stop at multiple newlines to prevent rambling
            }
        }
        
        try:
            response = requests.post(ollama_url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            if 'response' in result:
                log_message("Successfully received response from Ollama")
                return result['response'].strip()
            else:
                log_message("Invalid response format from Ollama", "ERROR")
                return None
                
        except requests.exceptions.ConnectionError:
            log_message("Could not connect to Ollama. Make sure Ollama is running on localhost:11434", "ERROR")
            return None
        except requests.exceptions.Timeout:
            log_message("Ollama request timed out", "ERROR")
            return None
        except Exception as e:
            log_message(f"Ollama request failed: {e}", "ERROR")
            return None
    
    def _run_openai(self, prompt: str, model: str = "openai") -> Optional[str]:
        """
        Run inference using OpenAI API.
        
        Args:
            prompt (str): The prompt to send
            model (str): Model identifier
        
        Returns:
            Optional[str]: Response from OpenAI or None if failed
        """
        if not self.openai_client or self.openai_client == "failed":
            log_message("OpenAI client not initialized or failed to initialize", "ERROR")
            return None
        
        # Default to gpt-3.5-turbo if just "openai" is specified
        openai_model = "gpt-3.5-turbo" if model == "openai" else model
        
        try:
            response = self.openai_client.chat.completions.create(
                model=openai_model,
                messages=[
                    {"role": "system", "content": "You are a professional resume writer and career advisor."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7,
                top_p=0.9
            )
            
            if response.choices and response.choices[0].message:
                log_message("Successfully received response from OpenAI")
                return response.choices[0].message.content.strip()
            else:
                log_message("Invalid response format from OpenAI", "ERROR")
                return None
                
        except Exception as e:
            log_message(f"OpenAI request failed: {e}", "ERROR")
            return None
    
    def _run_anthropic(self, prompt: str, model: str = "anthropic") -> Optional[str]:
        """
        Run inference using Anthropic API.
        
        Args:
            prompt (str): The prompt to send
            model (str): Model identifier
        
        Returns:
            Optional[str]: Response from Anthropic or None if failed
        """
        if not self.anthropic_client:
            log_message("Anthropic client not initialized", "ERROR")
            return None
        
        # Default to claude-3-sonnet if just "anthropic" is specified
        anthropic_model = "claude-3-sonnet-20240229" if model == "anthropic" else model
        
        try:
            response = self.anthropic_client.messages.create(
                model=anthropic_model,
                max_tokens=2000,
                temperature=0.7,
                system="You are a professional resume writer and career advisor.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            if response.content and response.content[0].text:
                log_message("Successfully received response from Anthropic")
                return response.content[0].text.strip()
            else:
                log_message("Invalid response format from Anthropic", "ERROR")
                return None
                
        except Exception as e:
            log_message(f"Anthropic request failed: {e}", "ERROR")
            return None
    
    def _run_groq(self, prompt: str, model: str = "groq") -> Optional[str]:
        """
        Run inference using Groq API.
        
        Args:
            prompt (str): The prompt to send
            model (str): Model identifier
        
        Returns:
            Optional[str]: Response from Groq or None if failed
        """
        # Check for API key
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            log_message("GROQ_API_KEY not found", "ERROR")
            return None
        
        # Default to llama3-8b if just "groq" is specified
        groq_model = "llama3-8b-8192" if model == "groq" else model
        
        # Use direct HTTP request to avoid OpenAI client version issues
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": groq_model,
            "messages": [
                {"role": "system", "content": "You are a professional resume writer and career advisor."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.3,
            "top_p": 0.8
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            if result.get('choices') and result['choices'][0].get('message'):
                log_message("Successfully received response from Groq")
                return result['choices'][0]['message']['content'].strip()
            else:
                log_message("Invalid response format from Groq", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            log_message(f"Groq request failed: {e}", "ERROR")
            return None
        except Exception as e:
            log_message(f"Groq request failed: {e}", "ERROR")
            return None
    
    def get_available_models(self) -> Dict[str, list]:
        """
        Get list of available models for each provider.
        
        Returns:
            Dict[str, list]: Dictionary of provider names and their available models
        """
        available = {}
        
        # Check Ollama availability
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                ollama_models = [model['name'] for model in response.json().get('models', [])]
                available['local'] = ollama_models if ollama_models else self.supported_models['local']
            else:
                available['local'] = []
        except:
            available['local'] = []
        
        # Check OpenAI availability
        if self.openai_client and self.openai_client != "failed":
            available['openai'] = self.supported_models['openai']
        else:
            available['openai'] = []
        
        # Check Anthropic availability
        if self.anthropic_client:
            available['anthropic'] = self.supported_models['anthropic']
        else:
            available['anthropic'] = []
        
        # Check Groq availability
        groq_api_key = os.getenv('GROQ_API_KEY')
        if groq_api_key and OPENAI_AVAILABLE:
            available['groq'] = self.supported_models['groq']
        else:
            available['groq'] = []
        
        return available
    
    def test_connection(self, model: str = "local") -> bool:
        """
        Test connection to a specific LLM provider.
        
        Args:
            model (str): Model identifier to test
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        test_prompt = "Hello"
        
        try:
            response = self.run_llm(test_prompt, model, max_retries=1)
            
            if response and len(response.strip()) > 0:
                log_message(f"Connection test passed for {model}")
                return True
            else:
                log_message(f"Connection test failed for {model} - no response", "WARNING")
                return False
        except Exception as e:
            log_message(f"Connection test failed for {model} - error: {e}", "ERROR")
            return False


# Convenience function for backward compatibility
def run_llm(prompt: str, model: str = "local") -> Optional[str]:
    """
    Convenience function to run LLM inference.
    
    Args:
        prompt (str): The prompt to send to the LLM
        model (str): Model identifier
    
    Returns:
        Optional[str]: LLM response or None if failed
    """
    interface = LLMInterface()
    return interface.run_llm(prompt, model)

