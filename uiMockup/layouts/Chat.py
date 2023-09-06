import streamlit as st
from interfaces import Bot
from components.BotSidebar import BotSidebar
from components.ChatBox import ChatBox

class Chat:

    def __init__(self, bot:Bot) -> None:
        self.bot = bot
        if f'{self.bot.uid}_messages' not in st.session_state:
            st.session_state[f'{self.bot.uid}_messages'] = []
        

    def display(self) -> None:
        BotSidebar(self.bot).display()
        ChatBox(self.bot).display()