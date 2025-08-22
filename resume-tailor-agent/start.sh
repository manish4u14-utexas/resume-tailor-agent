#!/bin/bash

# Resume Tailor Agent Startup Script

echo "🚀 Starting Resume Tailor Agent..."

# Start Ollama in background
echo "📡 Starting Ollama server..."
ollama serve &

# Wait a moment for Ollama to start
sleep 3

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source resume-tailor-env/bin/activate

# Start Streamlit
echo "🌐 Starting web interface..."
streamlit run streamlit_app.py

echo "✅ Resume Tailor Agent is running!"