#!/usr/bin/env python3
"""
Resume Tailor Agent - Streamlit Web Interface

This provides a user-friendly web interface for the Resume Tailor Agent.
"""

import streamlit as st
import os
import sys
import tempfile
from io import BytesIO
import traceback
import difflib
import re

# Add the src directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.resume_parser import ResumeParser
from src.llm_interface import LLMInterface
from src.utils import log_message


def setup_page():
    """Setup the Streamlit page configuration."""
    st.set_page_config(
        page_title="Resume Tailor Agent",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📄 Resume Tailor Agent")
    st.markdown("**Tailor your resume to specific job descriptions using AI**")
    st.markdown("<div style='text-align: center; color: #666; font-size: 0.9em; margin-bottom: 20px;'>Created by <strong>Manish Chaudhari</strong> 👨‍💻</div>", unsafe_allow_html=True)
    
    # Welcome message for new users
    with st.expander("🆕 New here? Click for quick start guide!", expanded=False):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("""
            ### 🚀 Quick Start (2 minutes)
            
            **Step 1: Get FREE AI Access**
            1. Visit [console.groq.com](https://console.groq.com)
            2. Sign up with email
            3. Copy your API key
            
            **Step 2: Use the Tool**
            1. Select "Groq API" in sidebar ⬅️
            2. Paste your API key
            3. Upload resume + job description
            4. Download tailored resume!
            
            **💻 Note:** Best experience on desktop/laptop
            """)
        
        with col2:
            st.markdown("""
            ### ❓ Why Groq?
            
            - ✅ **Completely FREE**
            - ⚡ **Super fast** (30 seconds)
            - 🎯 **High quality** results
            - 🔒 **No installation** needed
            - 📈 **6,000 requests/day** limit
            
            ### 💰 Other Options
            - **Local Ollama**: Free but requires setup
            - **OpenAI**: Paid but excellent quality
            - **Anthropic**: Paid, great for complex tasks
            """)
    
    # Add some styling with mobile responsiveness
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .step-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
    
    /* Mobile warning for very small screens */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 2rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def show_sidebar():
    """Show the sidebar with model selection and information."""
    st.sidebar.header("⚙️ Configuration")
    st.sidebar.markdown("---")
    st.sidebar.markdown("<div style='text-align: center; color: #888; font-size: 0.8em;'>🚀 Built by <strong>Manish Chaudhari</strong></div>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    # Model selection with better descriptions
    model_options = {
        "groq": "🚀 Groq API - FREE & FAST (Recommended)",
        "local": "🖥️ Local Ollama - FREE (Privacy)", 
        "openai": "💰 OpenAI GPT - PAID (Premium)",
        "anthropic": "💰 Anthropic Claude - PAID (Advanced)"
    }
    
    selected_model = st.sidebar.selectbox(
        "🤖 Choose Your AI Model:",
        options=list(model_options.keys()),
        format_func=lambda x: model_options[x],
        index=0,
        help="Groq is recommended for new users - it's free, fast, and high quality!"
    )
    
    # Show model information
    st.sidebar.markdown("### 📋 Model Information")
    
    if selected_model == "local":
        st.sidebar.info("""
        **Local Ollama** 🖥️
        - ✅ Completely FREE
        - ✅ Runs on your machine
        - ✅ Good for privacy
        - ⚠️ Requires Ollama installation
        - ⚠️ May be slower on older machines
        """)
        st.sidebar.markdown("""
        **📋 Setup Instructions:**
        1. Install Ollama from [ollama.ai](https://ollama.ai)
        2. Run: `ollama serve`
        3. Pull model: `ollama pull phi3:mini`
        4. Click "Test Connection" below
        """)
    elif selected_model == "groq":
        st.sidebar.success("""
        **Groq API** ⚡ (RECOMMENDED)
        - ✅ Completely FREE
        - ✅ Extremely fast (2-3 seconds)
        - ✅ High quality results
        - ✅ 6,000 requests/day limit
        - ✅ No installation needed
        """)
        st.sidebar.markdown("""
        **🚀 Quick Setup (2 minutes):**
        1. Visit [console.groq.com](https://console.groq.com)
        2. Sign up with email (free)
        3. Copy your API key
        4. Paste it below ⬇️
        """)
    elif selected_model == "openai":
        st.sidebar.warning("""
        **OpenAI GPT** 💰
        - ✅ Excellent quality
        - ✅ Very reliable
        - ✅ Fast processing
        - 💰 PAID service (~$0.01-0.05 per resume)
        - 🎁 $5 free credits for new users
        """)
        st.sidebar.markdown("""
        **💳 Setup Instructions:**
        1. Visit [platform.openai.com](https://platform.openai.com)
        2. Create account (get $5 free)
        3. Generate API key
        4. Paste it below ⬇️
        """)
    elif selected_model == "anthropic":
        st.sidebar.warning("""
        **Anthropic Claude** 💰
        - ✅ Excellent reasoning
        - ✅ Great for complex tasks
        - ✅ High quality output
        - 💰 PAID service (~$0.02-0.08 per resume)
        - 🎁 Free credits for new users
        """)
        st.sidebar.markdown("""
        **💳 Setup Instructions:**
        1. Visit [console.anthropic.com](https://console.anthropic.com)
        2. Create account (get free credits)
        3. Generate API key
        4. Paste it below ⬇️
        """)
    
    # API key input for services
    api_key = None
    if selected_model == "groq":
        api_key = st.sidebar.text_input(
            "🔑 Groq API Key:",
            type="password",
            placeholder="gsk_...",
            help="Get your FREE API key from console.groq.com (takes 2 minutes)"
        )
        if api_key:
            os.environ['GROQ_API_KEY'] = api_key
            st.sidebar.success("✅ API key entered!")
        else:
            st.sidebar.info("👆 Enter your Groq API key above to continue")
    elif selected_model == "openai":
        api_key = st.sidebar.text_input(
            "OpenAI API Key:",
            type="password",
            help="Enter your OpenAI API key"
        )
        if api_key:
            os.environ['OPENAI_API_KEY'] = api_key
    elif selected_model == "anthropic":
        api_key = st.sidebar.text_input(
            "Anthropic API Key:",
            type="password",
            help="Enter your Anthropic API key"
        )
        if api_key:
            os.environ['ANTHROPIC_API_KEY'] = api_key
    
    # Test connection button
    if st.sidebar.button("🔍 Test Connection"):
        test_llm_connection(selected_model)
    
    return selected_model


def test_llm_connection(model):
    """Test LLM connection and show results."""
    with st.sidebar:
        with st.spinner(f"Testing {model} connection..."):
            try:
                interface = LLMInterface()
                available_models = interface.get_available_models()
                
                if model in available_models and available_models[model]:
                    success = interface.test_connection(model)
                    if success:
                        st.success(f"✅ {model} connection successful!")
                    else:
                        st.error(f"❌ {model} connection failed")
                else:
                    st.error(f"❌ {model} not available or not configured")
                    
                    # Show setup instructions
                    if model == "local":
                        st.info("""
                        🖥️ **To use Local Ollama:**
                        1. Install Ollama from ollama.ai
                        2. Run: `ollama serve`
                        3. Run: `ollama pull phi3:mini`
                        4. Click "Test Connection" again
                        """)
                    elif model == "groq":
                        st.success("""
                        🚀 **To use Groq API (FREE):**
                        1. Visit console.groq.com
                        2. Sign up with email (takes 30 seconds)
                        3. Copy your API key
                        4. Paste it in the sidebar ⬅️
                        5. Click "Test Connection" again
                        """)
                    elif model == "openai":
                        st.warning("""
                        💰 **To use OpenAI (PAID):**
                        1. Visit platform.openai.com
                        2. Create account (get $5 free credits)
                        3. Generate API key
                        4. Paste it in the sidebar ⬅️
                        """)
                    elif model == "anthropic":
                        st.warning("""
                        💰 **To use Anthropic (PAID):**
                        1. Visit console.anthropic.com
                        2. Create account (get free credits)
                        3. Generate API key
                        4. Paste it in the sidebar ⬅️
                        """)
                        
            except Exception as e:
                st.error(f"❌ Connection test failed: {str(e)}")


def upload_resume():
    """Handle resume file upload."""
    st.markdown('<div class="step-header">📤 Step 1: Upload Your Resume</div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose your resume file (.docx format)",
        type=['docx'],
        help="Upload your resume in Microsoft Word (.docx) format"
    )
    
    if uploaded_file is not None:
        # Save uploaded file to temporary location
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, uploaded_file.name)
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"✅ Resume uploaded: {uploaded_file.name}")
        
        # Show resume preview
        with st.expander("📋 Preview Resume Sections", expanded=True):
            try:
                parser = ResumeParser(temp_path)
                if parser.load_document():
                    sections = parser.extract_sections()
                    
                    for section_name, content in sections.items():
                        if content.strip():
                            st.subheader(f"📝 {section_name.title()}")
                            # Show more content in preview
                            preview_content = content[:800] + "..." if len(content) > 800 else content
                            st.text_area(
                                f"{section_name.title()} Content:",
                                value=preview_content,
                                height=150,
                                disabled=True,
                                key=f"resume_preview_{section_name}"
                            )
                else:
                    st.error("Failed to load resume document")
            except Exception as e:
                st.error(f"Error previewing resume: {str(e)}")
        
        return temp_path
    
    return None


def input_job_description():
    """Handle job description input."""
    st.markdown('<div class="step-header">📝 Step 2: Provide Job Description</div>', unsafe_allow_html=True)
    
    input_method = st.radio(
        "How would you like to provide the job description?",
        ["Paste text directly", "Upload text file"],
        horizontal=True
    )
    
    jd_content = None
    
    if input_method == "Paste text directly":
        jd_content = st.text_area(
            "Job Description:",
            height=200,
            placeholder="Paste the job description here...",
            help="Copy and paste the job description from the job posting"
        )
    else:
        uploaded_jd = st.file_uploader(
            "Choose job description file (.txt format)",
            type=['txt'],
            help="Upload a text file containing the job description"
        )
        
        if uploaded_jd is not None:
            jd_content = str(uploaded_jd.read(), "utf-8")
            st.success(f"✅ Job description loaded: {uploaded_jd.name}")
    
    if jd_content and jd_content.strip():
        st.success(f"✅ Job description loaded ({len(jd_content)} characters)")
        
        with st.expander("📋 Preview Job Description", expanded=True):
            st.text_area(
                "Job Description Content:",
                value=jd_content[:1200] + "..." if len(jd_content) > 1200 else jd_content,
                height=200,
                disabled=True,
                key="jd_preview"
            )
        
        return jd_content.strip()
    
    return None


def tailor_resume(resume_path, jd_content, model):
    """Tailor the resume using the selected model."""
    st.markdown('<div class="step-header">🤖 Step 3: AI Resume Tailoring</div>', unsafe_allow_html=True)
    
    if st.button("🚀 Tailor My Resume", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Initialize components
            status_text.text("Initializing AI components...")
            progress_bar.progress(10)
            
            interface = LLMInterface()
            parser = ResumeParser(resume_path)
            
            # Step 2: Load and parse resume
            status_text.text("Loading and parsing resume...")
            progress_bar.progress(25)
            
            if not parser.load_document():
                st.error("❌ Failed to load resume document")
                return None
            
            sections = parser.extract_sections()
            non_empty_sections = {k: v for k, v in sections.items() if v.strip()}
            
            if not non_empty_sections:
                st.error("❌ No content sections found in resume")
                return None
            
            # Step 3: Build prompt
            status_text.text("Building AI prompt...")
            progress_bar.progress(40)
            
            sections_text = ""
            for section_name, content in non_empty_sections.items():
                sections_text += f"\n{section_name.upper()}:\n{content}\n"
            
            # Extract only summary and skills sections
            original_summary = ""
            original_skills = ""
            
            for section_name, content in sections.items():
                if 'summary' in section_name.lower() or 'profile' in section_name.lower():
                    original_summary = content
                elif 'skill' in section_name.lower() or 'competenc' in section_name.lower():
                    original_skills = content
            
            prompt = f"""
Add 2-3 job keywords to existing resume sections. DO NOT rewrite or expand.

JOB KEYWORDS TO ADD: {jd_content[:500]}

ORIGINAL SUMMARY:
{original_summary}

ORIGINAL SKILLS:
{original_skills}

TASK: Add only 2-3 relevant keywords from job description.

RULES:
- Keep EXACT same length and format
- Only replace/add 2-3 keywords
- Do NOT rewrite sentences
- Do NOT add new lines or bullets
- Keep all original content

SUMMARY:
[Original summary with 2-3 job keywords added]

SKILLS:
[Original skills with 2-3 new skills added]
"""
            
            # Step 4: Get AI response
            status_text.text(f"Getting AI response from {model}...")
            progress_bar.progress(60)
            
            response = interface.run_llm(prompt, model)
            
            if not response:
                st.error("❌ No response received from AI model")
                return None
            
            # Step 5: Parse response
            status_text.text("Processing AI response...")
            progress_bar.progress(80)
            
            # Parse only summary and skills from response
            tailored_sections = {}
            
            # Extract summary
            summary_match = re.search(r'SUMMARY:\s*\n(.*?)(?=\n\s*SKILLS:|$)', response, re.DOTALL | re.IGNORECASE)
            if summary_match:
                summary_content = summary_match.group(1).strip()
                # Find the original summary section name
                for section_name in sections.keys():
                    if 'summary' in section_name.lower() or 'profile' in section_name.lower():
                        tailored_sections[section_name] = summary_content
                        break
            
            # Extract skills  
            skills_match = re.search(r'SKILLS:\s*\n(.*?)$', response, re.DOTALL | re.IGNORECASE)
            if skills_match:
                skills_content = skills_match.group(1).strip()
                # Find the original skills section name
                for section_name in sections.keys():
                    if 'skill' in section_name.lower() or 'competenc' in section_name.lower():
                        tailored_sections[section_name] = skills_content
                        break
            
            # Step 6: Update resume
            status_text.text("Updating resume document...")
            progress_bar.progress(90)
            
            # Validate sections before updating
            valid_sections = {}
            for section_name, content in tailored_sections.items():
                original_content = sections.get(section_name, '')
                # Only update if content is reasonable length and actually different
                if content and len(content) <= len(original_content) * 1.5 and content.strip() != original_content.strip():
                    valid_sections[section_name] = content
                    st.info(f"✅ Updated {section_name} section")
                elif content.strip() == original_content.strip():
                    st.info(f"ℹ️ {section_name} section unchanged")
                else:
                    st.warning(f"⚠️ {section_name} was too different, keeping original")
            
            if not valid_sections:
                st.warning("ℹ️ No sections were updated - content may already be optimized or changes were too minimal")
                # Still save the original resume as "tailored" so user can download
                valid_sections = {k: v for k, v in sections.items() if k.lower() in ['summary', 'skills', 'professional summary', 'technical skills', 'core competencies']}
                
            if not parser.update_sections(valid_sections):
                st.error("❌ Failed to update resume sections")
                return None
            
            # Update tailored_sections for display
            if valid_sections:
                tailored_sections = valid_sections
            else:
                # Show original sections if no changes were made
                tailored_sections = {k: v for k, v in sections.items() if k.lower() in ['summary', 'skills', 'professional summary', 'technical skills', 'core competencies']}
            
            # Step 7: Save updated resume
            status_text.text("Saving tailored resume...")
            progress_bar.progress(95)
            
            output_path = os.path.join(tempfile.mkdtemp(), "tailored_resume.docx")
            if not parser.save_document(output_path):
                st.error("❌ Failed to save updated resume")
                return None
            
            progress_bar.progress(100)
            status_text.text("✅ Resume tailoring completed!")
            
            st.success("🎉 Resume successfully tailored! Only summary and skills sections were updated.")
            
            # Show tailored sections with diff highlighting
            st.markdown("### 📋 Updated Sections (Summary & Skills Only)")
            for section_name, content in tailored_sections.items():
                if content.strip():
                    with st.expander(f"📝 {section_name.title()} (Updated)", expanded=True):
                        # Show original vs updated with highlighting
                        original_content = sections.get(section_name, "")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Original:**")
                            st.text_area(
                                "Original",
                                value=original_content,
                                height=150,
                                disabled=True,
                                key=f"original_{section_name}",
                                label_visibility="collapsed"
                            )
                        
                        with col2:
                            st.markdown("**Updated:**")
                            st.text_area(
                                "Updated",
                                value=content,
                                height=150,
                                disabled=True,
                                key=f"tailored_{section_name}",
                                label_visibility="collapsed"
                            )
                        
                        # Show highlighted differences
                        st.markdown("**🔍 Changes Highlighted:**")
                        if original_content.strip() and content.strip():
                            diff_html = show_diff_highlighting(original_content, content)
                            st.markdown(diff_html, unsafe_allow_html=True)
                        else:
                            st.info("No content to compare")
                        
                        # Show simple word count comparison
                        original_words = len(original_content.split())
                        updated_words = len(content.split())
                        word_diff = updated_words - original_words
                        
                        if word_diff > 0:
                            st.success(f"📈 Added {word_diff} words to this section")
                        elif word_diff < 0:
                            st.info(f"📉 Removed {abs(word_diff)} words from this section")
                        else:
                            st.info("📊 Word count unchanged")
            
            return output_path
            
        except Exception as e:
            st.error(f"❌ Error during resume tailoring: {str(e)}")
            st.error("Full error details:")
            st.code(traceback.format_exc())
            return None
    
    return None


def show_diff_highlighting(original, updated):
    """Show differences between original and updated text with color highlighting."""
    if not original.strip() or not updated.strip():
        return "<p>No comparison available</p>"
    
    # Split into sentences for better context
    original_sentences = re.split(r'[.!?]\s+', original.strip())
    updated_sentences = re.split(r'[.!?]\s+', updated.strip())
    
    # Create diff
    differ = difflib.SequenceMatcher(None, original_sentences, updated_sentences)
    
    result_html = "<div style='font-family: Arial, sans-serif; line-height: 1.8; padding: 15px; background-color: #f8f9fa; border-radius: 8px; border-left: 4px solid #007bff;'>"
    
    changes_found = False
    
    for tag, i1, i2, j1, j2 in differ.get_opcodes():
        if tag == 'equal':
            # Unchanged text - show with normal styling
            for sentence in original_sentences[i1:i2]:
                if sentence.strip():
                    result_html += f"<span style='color: #495057;'>{sentence.strip()}.</span> "
        elif tag == 'delete':
            # Removed text (red background)
            changes_found = True
            for sentence in original_sentences[i1:i2]:
                if sentence.strip():
                    result_html += f"<span style='background-color: #f8d7da; color: #721c24; text-decoration: line-through; padding: 2px 4px; border-radius: 3px; margin: 2px;'>{sentence.strip()}.</span> "
        elif tag == 'insert':
            # Added text (green background)
            changes_found = True
            for sentence in updated_sentences[j1:j2]:
                if sentence.strip():
                    result_html += f"<span style='background-color: #d4edda; color: #155724; font-weight: bold; padding: 2px 4px; border-radius: 3px; margin: 2px; border: 1px solid #c3e6cb;'>{sentence.strip()}.</span> "
        elif tag == 'replace':
            # Changed text (show both)
            changes_found = True
            for sentence in original_sentences[i1:i2]:
                if sentence.strip():
                    result_html += f"<span style='background-color: #f8d7da; color: #721c24; text-decoration: line-through; padding: 2px 4px; border-radius: 3px; margin: 2px;'>{sentence.strip()}.</span> "
            for sentence in updated_sentences[j1:j2]:
                if sentence.strip():
                    result_html += f"<span style='background-color: #d4edda; color: #155724; font-weight: bold; padding: 2px 4px; border-radius: 3px; margin: 2px; border: 1px solid #c3e6cb;'>{sentence.strip()}.</span> "
    
    result_html += "</div>"
    
    # Add summary of changes
    if changes_found:
        summary = "<div style='margin-top: 10px; padding: 10px; background-color: #e7f3ff; border-radius: 5px; border-left: 3px solid #007bff;'><strong>📝 Changes Summary:</strong> Keywords and phrases have been added/modified to better match the job requirements.</div>"
    else:
        summary = "<div style='margin-top: 10px; padding: 10px; background-color: #fff3cd; border-radius: 5px; border-left: 3px solid #ffc107;'><strong>ℹ️ No Changes:</strong> The content appears to be identical or very similar.</div>"
    
    # Add legend
    legend = """
    <div style='margin-top: 10px; font-size: 0.9em; display: flex; gap: 15px;'>
        <span style='background-color: #d4edda; color: #155724; padding: 4px 8px; border-radius: 4px; border: 1px solid #c3e6cb;'>✅ Added/New Content</span>
        <span style='background-color: #f8d7da; color: #721c24; padding: 4px 8px; border-radius: 4px; border: 1px solid #f5c6cb;'>❌ Removed Content</span>
    </div>
    """
    
    return result_html + summary + legend


def download_resume(output_path):
    """Provide download link for the tailored resume."""
    if output_path and os.path.exists(output_path):
        st.markdown('<div class="step-header">⬇️ Step 4: Download Your Tailored Resume</div>', unsafe_allow_html=True)
        
        with open(output_path, "rb") as file:
            btn = st.download_button(
                label="📥 Download Tailored Resume",
                data=file.read(),
                file_name="tailored_resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        
        st.success("✅ Your tailored resume is ready for download!")
        st.markdown("<div style='text-align: center; color: #666; font-size: 0.8em; margin-top: 10px;'>Resume tailored using AI • Created by Manish Chaudhari</div>", unsafe_allow_html=True)


def main():
    """Main Streamlit application."""
    setup_page()
    
    # Single consolidated notice for first-time users
    if 'first_visit' not in st.session_state:
        st.session_state.first_visit = True
        st.info("👋 **New here?** This tool safely updates only your Summary & Skills sections (experience untouched). Works best on desktop. Expand the guide above to get started!")
    
    # Show sidebar
    selected_model = show_sidebar()
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Step 1: Upload resume
        resume_path = upload_resume()
        
        # Step 2: Input job description
        jd_content = input_job_description()
        
        # Step 3: Tailor resume (only if both inputs are provided)
        output_path = None
        if resume_path and jd_content:
            output_path = tailor_resume(resume_path, jd_content, selected_model)
        
        # Step 4: Download tailored resume
        if output_path:
            download_resume(output_path)
    
    with col2:
        # Clean sidebar info
        st.markdown("💻 **Desktop Recommended** for best experience")
        st.markdown("---")
        
        st.markdown("### 📚 How It Works")
        st.markdown("""
        1. 🤖 **Choose AI Model** (Groq recommended)
        2. 🔑 **Enter API Key** (free for Groq)
        3. 📄 **Upload Resume** (.docx format)
        4. 📋 **Paste Job Description**
        5. ✨ **Click "Tailor My Resume"**
        6. 📥 **Download** your optimized resume
        """)
        
        st.markdown("### 🎯 Why Use This Tool?")
        st.markdown("""
        - 🎯 **Conservative**: Only updates Summary & Skills
        - 📄 **Professional**: Keeps your exact formatting
        - ⚡ **Fast**: Results in 30 seconds (Groq)
        - 🆓 **Free Options**: Groq & Local Ollama
        - 🔒 **Private**: Your data stays secure
        - 🛡️ **Safe**: Experience section untouched
        """)
        
        st.markdown("### 🆕 New User? Start Here!")
        st.markdown("""
        **Recommended for beginners:**
        1. 🚀 Select "Groq API" (FREE & FAST)
        2. 📝 Get free key at console.groq.com
        3. 📄 Upload your resume (.docx)
        4. 📋 Paste job description
        5. ✨ Get tailored resume!
        """)
        
        st.markdown("### 💡 Pro Tips")
        st.markdown("""
        - Use complete job descriptions for better results
        - Ensure resume has clear Summary and Skills sections
        - Only Summary and Skills will be modified
        - Review AI suggestions before using
        - Keep original resume as backup
        """)
    
    # Add copyright footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #888; font-size: 0.8em; padding: 20px;'>" 
        "© 2025 Manish Chaudhari. All rights reserved. | Resume Tailor Agent<br>"
        "<small>💻 Best viewed on desktop/laptop devices</small>"
        "</div>", 
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

