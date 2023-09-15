import os
import streamlit as st
import json
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

def handleAuth():
    cipher_suite = Fernet(os.getenv('CIPHER_KEY').encode())
    if 'data' not in st.experimental_get_query_params():
        testUserInfo = json.dumps({'name': 'Test User 1', 'username': 'testuser1'})
        encryptedUserInfo = cipher_suite.encrypt(testUserInfo.encode())
        st.experimental_set_query_params(data=encryptedUserInfo.decode())

    encryptedUserInfo = st.experimental_get_query_params()['data'][0].encode()
    try:
        if encryptedUserInfo != json.dumps({'name': 'Test User 1', 'username': 'testuser1'}).encode():
            decryptedUserInfo = cipher_suite.decrypt(encryptedUserInfo).decode()
        else:
            decryptedUserInfo = json.dumps({'name': 'Test User 1', 'username': 'testuser1'})
        parsedUserInfo = json.loads(decryptedUserInfo)
        st.session_state['active_user'] = parsedUserInfo['username'].split('@')[0]
        st.session_state['active_user_name'] = parsedUserInfo['name']
    except Exception as e:
        st.title('BotCraft Studios')
        st.error("Tried loading an invalid user")
        st.exception(e)


if __name__ == "__main__":
    handleAuth()
    if 'active_user' in st.session_state:
        Router().display()