import streamlit as st
import os
from typing import List
from azure.storage.blob import BlobServiceClient

from components.BotCard import BotCard

class Dashboard:
    def __init__(self) -> None:
        st.set_page_config(
        page_title="Dashboard",
        page_icon=":robot_face",
        layout="centered")
        self.blobClient = BlobServiceClient.from_connection_string(os.environ['BLOB_STORAGE_CONNECTION_STRING'])

    def display(self) -> None:
        st.title("BotCraft Studio")
        st.subheader(f"Hey {st.session_state['active_user_name']}")
        st.caption("Chat with an existing bot, or create a new bot")

        st.header("Your bots")

        if st.button("Create a New Bot"):
            st.session_state['activePage'] = 'createBot'
            st.experimental_rerun()
        
        with st.spinner("Fetching your bots..."):
            bots = self._getBots()

        if len(bots):
            cols = st.columns(3)
            for i, botId in enumerate(bots):
                with cols[i%3]:
                    BotCard(botId).display()
        else:
            st.caption("You have no bots yet. Create a new one to get started!")

    def _getBots(self) -> List[str]:
        currentUser = st.session_state['active_user']
        try:
            userContainerClient = self.blobClient.create_container(currentUser)
        except:
            userContainerClient = self.blobClient.get_container_client(currentUser)

        allBlobs = userContainerClient.list_blob_names()
        userBots = list(set([blob.split("/")[0] for blob in allBlobs]))
        return userBots