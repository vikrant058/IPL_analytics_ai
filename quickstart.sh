#!/bin/bash

# IPL Analytics AI Platform - Quick Start Guide

echo "🏏 IPL Analytics AI Platform - Setup & Quick Start"
echo "=================================================="
echo ""

# Check Python version
echo "✓ Checking Python version..."
python3 --version

# Install dependencies
echo ""
echo "✓ Installing dependencies..."
pip install -r requirement.txt > /dev/null 2>&1

# Test data loading
echo ""
echo "✓ Testing data loader..."
python3 << 'EOF'
from data_loader import IPLDataLoader

loader = IPLDataLoader()
matches, deliveries = loader.load_data()
matches, deliveries = loader.preprocess_data()
summary = loader.get_summary_stats()

print(f"   Dataset Summary:")
print(f"   - Total Matches: {summary['total_matches']}")
print(f"   - Seasons: {summary['seasons']}")
print(f"   - Teams: {summary['teams']}")
print(f"   - Venues: {summary['venues']}")
EOF

echo ""
echo "=================================================="
echo ""
echo "🚀 Ready to use! Choose one:"
echo ""
echo "1. Run Streamlit Dashboard:"
echo "   $ streamlit run app.py"
echo ""
echo "2. Run FastAPI Server:"
echo "   $ python api.py"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "3. Use as Python Library:"
echo "   from data_loader import IPLDataLoader"
echo "   from ai_engine import AIEngine"
echo ""
echo "💡 See README.md for detailed documentation"
echo ""
