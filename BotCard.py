import streamlit as st


class BotCard:

    def __init__(self, botId):

        self.botId = botId

    def display(self, router):
        with st.form(key=f'{self.botId}_card'):
            botName = self.botId.split('-')[0]
            st.subheader(botName)
            buttonCols = st.columns(2)
            with buttonCols[0]:
                if st.form_submit_button('Chat'):
                    router.redirect(f'/chat/{self.botId}')
            with buttonCols[1]:
                if st.form_submit_button("Delete", type='primary'):
                    # TODO: Implement Delete Logic
                    pass
                