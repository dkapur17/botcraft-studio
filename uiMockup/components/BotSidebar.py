import streamlit as st
from interfaces import Bot

class BotSidebar:

    def __init__(self, bot:Bot):
        self.bot = bot

    def display(self) -> None:
        st.sidebar.button("Back to Dashboard", on_click=self._onBackClick)
        st.sidebar.title(self.bot.name)
        st.sidebar.image(self.bot.img, width=100)
        st.sidebar.caption(self.bot.desc)
        st.sidebar.file_uploader("Add a file to the Knowledge Base")
        st.sidebar.subheader("Current Knowledge Base")
        fileList = ['KT.mp4', 'Azure.txt', 'Recording.mp3', 'Docs.pdf']
        fileListMD = '\n'.join([f'- [{file}]({file})' for file in fileList])
        st.sidebar.markdown(fileListMD)

    def _onBackClick(self) -> None:
        botId = st.session_state['active_bot'].uid
        del st.session_state[f'{botId}_messages']
        del st.session_state['active_bot']