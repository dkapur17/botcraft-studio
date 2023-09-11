import streamlit as st

class ChatBox:

    def __init__(self, botId):
        self.botId = botId

    def display(self):
        
        for message in st.session_state[f'{self.botId}_messages']:
            with st.chat_message(message["role"]):
                st.markdown(message['content'])

        if query := st.chat_input("What would you like to know?"):
            with st.chat_message("user"):
                st.markdown(query)
            
            chatHistory = st.session_state[f'{self.botId}_messages']
            chatHistory.append({'role': 'user', 'content': query})
            chatHistory.append(self.getAnswer(chatHistory))
            st.session_state[f'{self.botId}_messages'] = chatHistory
            st.experimental_rerun()

    def getAnswer(self, chatHistory):
        
        # TODO: Write business logic for getting answer
        lastQuery = chatHistory[-1]['content']
        response = {'role': 'assistant', 'content': lastQuery}

        return response