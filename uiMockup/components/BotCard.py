from interfaces.Bot import Bot
import streamlit as st


class BotCard:

    def __init__(self, bot: Bot):
        self.bot = bot

    def display(self) -> None:
        with st.form(f'{self.bot.uid}_card'):
            st.title(self.bot.name)
            st.image(self.bot.img, use_column_width='always')
            st.caption(self.bot.desc)
            st.form_submit_button('Chat', on_click=self._onChatClick)

    def _onChatClick(self) -> None:
        st.session_state['active_bot'] = self.bot