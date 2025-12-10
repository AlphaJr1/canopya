#!/bin/bash

# Script untuk menjalankan Database Viewer Dashboard

echo "🗄️  Starting Aeropon Database Viewer..."
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "⚠️  Streamlit not found. Installing..."
    pip install streamlit
fi

# Run dashboard
streamlit run database_viewer.py --server.port 8501

echo ""
echo "✅ Dashboard stopped"
