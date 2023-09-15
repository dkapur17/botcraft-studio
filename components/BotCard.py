import streamlit as st
import os
from azure.storage.blob import BlobServiceClient, BlobPrefix
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient

class BotCard:

    def __init__(self, botId):
        self.botId = botId
        self.blobClient = BlobServiceClient.from_connection_string(os.environ['BLOB_STORAGE_CONNECTION_STRING'])

    def display(self):
        with st.form(key=f'{self.botId}_card'):
            botName = self.botId.split('||==||')[0]
            st.subheader(botName)
            buttonCols = st.columns(2)
            with buttonCols[0]:
                if st.form_submit_button('Chat'):
                    st.session_state['activeBotId'] = self.botId
                    st.session_state['activePage'] = 'chat'
                    st.experimental_rerun()
            with buttonCols[1]:
                if st.form_submit_button("Delete", type='primary'):
                    # TODO: Implement Delete Logic
                    # Delete the folder within the active user container
                    userContainerClient = self.blobClient.get_container_client(st.session_state['active_user'])
                    blobsForBot = userContainerClient.list_blobs(name_starts_with=self.botId)
                    for blob in blobsForBot:
                        userContainerClient.delete_blob(blob.name)                
                    # Delete the Search Index associated with the bot if it exists
                    credential = AzureKeyCredential(os.environ['AZURE_COGNITIVE_SEARCH_KEY'])
                    searchIndexCient = SearchIndexClient(endpoint=os.environ['AZURE_COGNITIVE_SEARCH_ENDPOINT'], credential=credential)
                    try:
                        searchIndexCient.delete_index(index = self.botId.lower())
                    except:
                        pass
                    st.experimental_rerun()
                        