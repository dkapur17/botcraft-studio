#!/bin/bash
streamlit run /app/main.py &
nginx -g "daemon off;"