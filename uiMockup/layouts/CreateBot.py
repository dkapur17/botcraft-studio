import streamlit as st

class CreateBot:

    def __init__(self):
        pass
    
    def display(self):
        st.button("Back to Dashboard", on_click=self._onBackClick)
        st.title("Create a Bot")
        with st.form('create_bot'):
            st.text_input('Bot Name')
            st.text_area('Bot Description')
            st.file_uploader('Bot Image')
            st.form_submit_button('Create Bot')


    def _onBackClick(self):
        del st.session_state['active_bot']