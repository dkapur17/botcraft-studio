import streamlit as st

# Hide unwanted components as fast as possible
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    </style>
    """
st.markdown(hide_st_style, unsafe_allow_html=True)

import os
import json
from dotenv import load_dotenv

from Dashboard import Dashboard
from CreateBot import CreateBot
from Chat import Chat

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import base64


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

def decrypt(data):
    key = os.environ['PRIVATE_KEY'].encode()
    data = base64.b64decode(data.encode())
    rsakey = RSA.importKey(key)
    rsakey = PKCS1_v1_5.new(rsakey)
    return rsakey.decrypt(data, 'bollox').decode()

def handleAuth():
    if 'data' not in st.experimental_get_query_params():
        st.experimental_set_query_params(data=os.environ['DEFAULT_USER_DATA'])

    encryptedUserInfo = st.experimental_get_query_params()['data'][0]
    try:
        decryptedUserInfo = decrypt(encryptedUserInfo)
        parsedUserInfo = json.loads(decryptedUserInfo)
        st.session_state['active_user'] = parsedUserInfo['username'].split('@')[0]
        st.session_state['active_user_name'] = parsedUserInfo['name']
    except Exception as e:
        st.error("Can't access the app from here. Go to https://botcraftstudio.azurewebsites.net/ to access the app.")
        # st.title('BotCraft Studio')
        # st.error("Tried loading an invalid user")
        # st.exception(e)


if __name__ == "__main__":
    handleAuth()
    if 'active_user' in st.session_state:
        Router().display()