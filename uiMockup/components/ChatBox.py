import streamlit as st
from interfaces import Bot

class ChatBox:

    def __init__(self, bot:Bot):
        self.bot = bot

    def display(self):
        
        for message in st.session_state[f'{self.bot.uid}_messages']:
            with st.chat_message(message["role"]):
                st.markdown(message['content'])

        if prompt := st.chat_input("Ask me anything!"):
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state[f'{self.bot.uid}_messages'].extend([
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": prompt}
            ])
            st.experimental_rerun()