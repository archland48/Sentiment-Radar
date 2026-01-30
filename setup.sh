#!/bin/bash

# Setup script for Sentiment Alpha Radar

echo "🚀 Setting up Sentiment Alpha Radar..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Download TextBlob corpora
echo "📚 Downloading TextBlob corpora..."
python -m textblob.download_corpora

echo "✅ Setup complete!"
echo ""
echo "To run the application:"
echo "  uvicorn main:app --reload"
echo ""
echo "Then open http://localhost:8000 in your browser"
