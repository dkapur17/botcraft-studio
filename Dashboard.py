import streamlit as st
from uuid import uuid1
from typing import List

class Dashboard:

    def init(self) -> None:
        st.set_page_config(
        page_title="Dashboard",
        page_icon=":robot_face",
        layout="centered")

    def display(self, router) -> None:
        st.title("GoBot")
        st.caption("Chat with an existing bot, or create a new bot")

        st.header("Your bots")
        bots = self._getBots()
        if st.button("Create a New Bot"):
            router.redirect('/createBot')

        cols = st.columns(3)
        for col, botId in zip(cols, bots):
            with col:
                with st.form(key=f'{botId}_card'):
                    botName = botId.split('-')[0]
                    st.subheader(botName)
                    if st.form_submit_button('Chat'):
                        router.redirect(f'/chat/{botId}')

    def _getBots(self) -> List[str]:
        # TODO: Get list of bots for the current user from blob storage
        return ['AlphaZero-e3a59a6f-2163-41b0-bf24-60de569001a0']