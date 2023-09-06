import streamlit as st
from layouts.Dashboard import Dashboard
from layouts.Chat import Chat
from layouts.CreateBot import CreateBot

if 'active_bot' not in st.session_state:
    Dashboard().display()
elif st.session_state['active_bot'] is None:
    CreateBot().display()
else:
    Chat(st.session_state['active_bot']).display()