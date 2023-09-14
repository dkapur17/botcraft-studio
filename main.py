import os
import streamlit as st
from dotenv import load_dotenv

from Dashboard import Dashboard
from CreateBot import CreateBot
from Chat import Chat

from cryptography.fernet import Fernet


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
    cipher_suite = Fernet(os.getenv('CIPHER_KEY').encode())
    encryptedAlias = st.experimental_get_query_params()['alias'][0].encode()

    try:
    # Backdoor
        if encryptedAlias != 'testuser1'.encode():
            decryptedAlias = cipher_suite.decrypt(encryptedAlias)
        else:
            decryptedAlias = encryptedAlias
        st.session_state['active_user'] = decryptedAlias.decode()
        Router().display()
    except:
        st.title('BotCraft Studios')
        st.error("Tried loading an invalid user")
    
