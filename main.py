import streamlit as st
from dotenv import load_dotenv

from Dashboard import Dashboard
from CreateBot import CreateBot
from Chat import Chat

load_dotenv()

class Router:

    def __init__(self):
        pass

    def display(self):

        if 'activePage' not in st.session_state:
            st.session_state['activePage'] = 'dashboard'
        if st.session_state['activePage'] == 'dashboard':
            Dashboard().display()
        elif st.session_state['activePage'] == 'chat':
            Chat(st.session_state['activeBotId']).display()
        elif st.session_state['activePage'] == 'createBot':
            CreateBot().display()


if __name__ == "__main__":

    st.session_state['active_user'] = 'testuser1'
    Router().display()
    
