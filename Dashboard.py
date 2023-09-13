import streamlit as st
import os
from typing import List
from azure.storage.blob import BlobServiceClient

from BotCard import BotCard

class Dashboard:
    def __init__(self) -> None:
        st.set_page_config(
        page_title="Dashboard",
        page_icon=":robot_face",
        layout="centered")
        self.blobClient = BlobServiceClient.from_connection_string(os.environ['BLOB_STORAGE_CONNECTION_STRING'])

    def display(self, router) -> None:
        st.title("BotCraft Studio")
        st.caption("Chat with an existing bot, or create a new bot")

        st.header("Your bots")
        bots = self._getBots()
        if st.button("Create a New Bot"):
            router.redirect('/createBot')

        cols = st.columns(3)
        for i, botId in enumerate(bots):
            with cols[i%3]:
                BotCard(botId).display(router)

    def _getBots(self) -> List[str]:
        currentUser = st.session_state['active_user']
        userContainerClient = self.blobClient.get_container_client(currentUser)
        allBlobs = userContainerClient.list_blob_names()
        userBots = list(set([blob.split("/")[0] for blob in allBlobs]))
        return userBots