#!/bin/bash

# Start FastAPI in the background
uvicorn backend.api:app --host 0.0.0.0 --port 8000 &

# Start Streamlit
streamlit run frontend/prompt_manager.py --server.port 8501 --server.address 0.0.0.0 