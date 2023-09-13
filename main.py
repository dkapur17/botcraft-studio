import streamlit as st
from streamlit_router import StreamlitRouter
from dotenv import load_dotenv

from Dashboard import Dashboard
from CreateBot import CreateBot
from Chat import Chat

load_dotenv()

router = StreamlitRouter()

@router.map('/', ['GET'])
def _index():
    Dashboard().display(router)

@router.map('/createBot', ['GET'])
def _createBot():
    CreateBot().display(router)

@router.map('/chat/<string:botid>', ['GET'])
def _chat(botid):
   Chat(botid).display(router)


if __name__ == "__main__":

    st.session_state['active_user'] = 'testuser1'
    router.serve()
