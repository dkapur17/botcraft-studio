import streamlit as st

class BotSidebar:

    def __init__(self, botId):
        
        self.botId = botId
        self.botName = botId.split('-')[0]
        self.fileList = self.getFiles()

    def display(self, router) -> None:
        with st.sidebar:
            if st.button("Back to Dashboard"):
                router.redirect('/')
            st.title(self.botName)
            if st.button('Clear Chat'):
                st.session_state[f'{self.botId}_messages'] = []
            
            with st.form(f'{self.botId}_uploader'):
                files = st.file_uploader("Add a file to the Knowledge Base")
                if st.form_submit_button("Upload"):
                    with st.spinner('Adding Documents to Knowledge Base...'):
                        self.uploadFiles(files)
            st.subheader("Current Knowledge Base")
            fileListMD = '\n'.join([f'- [{file}]({file})' for file in self.fileList])
            st.markdown(fileListMD)

    def getFiles(self):
        # TODO: Fetch file list from blob storage
        return []
    
    def uploadFiles(self):
        # TODO: Upload new files to storage and index them
        return