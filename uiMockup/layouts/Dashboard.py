import streamlit as st
from uuid import uuid1
from typing import List
from interfaces.Bot import Bot
from components.BotCard import BotCard

class Dashboard:

    def init(self) -> None:
        pass

    def display(self) -> None:
        st.title("GoBot")
        st.caption("Chat with an existing bot, or create a new bot")

        st.header("Your bots")
        bots = self._getBots()
        st.button("Create a New Bot", on_click=self._onCreateClick)

        nCols = 3
        botCols = st.columns(nCols)
        for i, bot in enumerate(bots):
            with botCols[i % nCols]:
                BotCard(bot).display()

    def _getBots(self) -> List[Bot]:

        return [
            Bot(str(uuid1()),"Delta 1","A short description about the bot","https://media.istockphoto.com/vectors/-vector-id1010001882?k=6&m=1010001882&s=612x612&w=0&h=hjArrtcMrHNjzF0CIR75SCp1_02fra9JvZqZJt5oggI="),
            Bot(str(uuid1()),"Delta 2","A short description about the bot","https://media.istockphoto.com/vectors/-vector-id1010001882?k=6&m=1010001882&s=612x612&w=0&h=hjArrtcMrHNjzF0CIR75SCp1_02fra9JvZqZJt5oggI="),
            Bot(str(uuid1()),"Delta 3","A short description about the bot","https://media.istockphoto.com/vectors/-vector-id1010001882?k=6&m=1010001882&s=612x612&w=0&h=hjArrtcMrHNjzF0CIR75SCp1_02fra9JvZqZJt5oggI="),
        ]
    
    def _onCreateClick(self) -> None:
        st.session_state['active_bot'] = None