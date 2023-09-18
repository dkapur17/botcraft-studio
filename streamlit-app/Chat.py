import streamlit as st
from components.BotSidebar import BotSidebar
from components.Chatbox import ChatBox

class Chat:

    def __init__(self, botId):
        # st.set_page_config(
        # page_title="Chat",
        # page_icon=":speech_balloon:",
        # layout="centered")

        self.botId = botId
        self.botName = botId.split('-')[0]

        if f'{botId}_messages' not in st.session_state:
            st.session_state[f'{botId}_messages'] = []

    def display(self):
        BotSidebar(self.botId).display()
        ChatBox(self.botId).display()