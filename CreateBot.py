import os
import io
import streamlit as st
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from uuid import uuid4
from joblib import Parallel, delayed
from pdfminer.high_level import extract_text
import cleantext
from time import sleep

load_dotenv()


st.session_state['active_user'] = 'testuser1'

class CreateBot:
    def __init__(self):

        self.blobClient = BlobServiceClient.from_connection_string(os.environ['BLOB_STORAGE_CONNECTION_STRING'])

    def display(self):

        st.title("BotCraft Studio") 
        st.header('Create a new Bot')

        if 'waitingOnBotCreation' not in st.session_state:
            with st.form("Bot Creation Form"):
                
                botName = st.text_input('Bot Name', key='bot_name', placeholder='Give your bot a name')
                files = st.file_uploader('Upload the documents making up your knowledge base', accept_multiple_files=True, type=['pdf', 'docx', 'doc', 'mp4', 'txt', 'mp3'], key='upload_kb')
                
                if st.form_submit_button("Create Bot"):
                    # self.initBot(botName, files)
                    st.session_state['createBotInfo'] = {'botName': botName, 'files': files}
                    st.session_state['waitingOnBotCreation'] = True
                    st.experimental_rerun()
        else:
            with st.spinner("Creating Bot..."):
                statusText = st.empty()
                self.initBot(st.session_state['createBotInfo']['botName'], st.session_state['createBotInfo']['files'], statusText)
            statusText.success("Bot Created!")

    def initBot(self, botName, files, statusText):
        
        botId = str(uuid4())
        containerClient = self.blobClient.get_container_client(st.session_state['active_user'])
        # containerClient.upload_blob(name=f'{botName}-{botId}/id.txt', data=botId, overwrite=True)
        
        statusText.info("Uploading Files...")
        Parallel(n_jobs=-1)(delayed(self.uploadFile)(botName, botId, file, containerClient) for file in files)
        statusText.empty()

        statusText.info("Extracting Content from Files...")
        texts = Parallel(n_jobs=-1)(delayed(self.extractTextFromFiles)(file) for file in files)
        statusText.empty()

        statusText.info("Uploading Text Content...")
        Parallel(n_jobs=-1)(delayed(self.uploadText)(botName, botId, file, text, containerClient) for file, text in zip(files, texts))
        statusText.empty()

        statusText.info("Vectorizing and Pushing to Database...")
        Parallel(n_jobs=-1)(delayed(self.vectorizeAndPush)(botName, botId, file, text, containerClient) for file, text in zip(files, texts))
        statusText.empty()

        statusText.success("Bot Created!")

    def uploadFile(self, botName, botId, file, containerClient):
        containerClient.upload_blob(name=f'{botName}-{botId}/{file.name}', data=file, overwrite=True)
    
    def extractTextFromFiles(self, file):
        # Process file to get text
        if file.type == 'application/pdf':
            textContent = self._processPDF(file)
        elif file.type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            textContent = self._processWord(file)
        elif file.type == 'video/mp4':
            textContent = self._processVideo(file)
        elif file.type == 'audio/mpeg':
            textContent = self._processAudio(file)
        elif file.type == 'text/plain':
            textContent = self._processText(file)

        return textContent
    
    def uploadText(self, botName, botId, file, text, containerClient):
        containerClient.upload_blob(name=f'{botName}-{botId}/{file.name}.txt', data=text, overwrite=True)


    def vectorizeAndPush(self, botName, botId, file, text, containerClient):
        pass

    def _processPDF(self, pdfFile):
        extractedText = extract_text(pdfFile)
        cleanedText = cleantext.clean(extractedText, clean_all=False, extra_spaces=True, stemming=False, stopwords=False, lowercase=False, numbers=False, punct=False, reg='\n', reg_replace=' ')
        return cleanedText

    def _processWord(self, wordFile):
        return 'Yet to implement word file'
    
    def _processVideo(self, videoFile):
        return 'Yet to implement video file'

    def _processAudio(self, audioFile):
        return 'Yet to implement audio file'

    def _processText(self, textFile):
        return '\n'.join(textFile.readlines())


st.set_page_config(
    page_title="Create a new Bot",
    page_icon=":robot_face:",
    layout="centered")

CreateBot().display()