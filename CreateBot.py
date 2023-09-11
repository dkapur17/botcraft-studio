import os
import io
import streamlit as st
import cleantext
import openai
import textract

from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SimpleField, SearchableField, SearchField, SearchFieldDataType, VectorSearch, HnswVectorSearchAlgorithmConfiguration, SearchIndex
from dotenv import load_dotenv
from uuid import uuid4
from joblib import Parallel, delayed
from time import sleep
from MediaHandler import MediaHandler


from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import AzureSearch
from langchain.text_splitter import TokenTextSplitter
from langchain.docstore.document import Document

from utils import TempFilePath

load_dotenv()


class CreateBot:
    def __init__(self):
        st.set_page_config(
        page_title="Create a new Bot",
        page_icon=":robot_face:",
        layout="centered")

        self.blobClient = BlobServiceClient.from_connection_string(os.environ['BLOB_STORAGE_CONNECTION_STRING'])
        self.mediaHandler = MediaHandler(blobClient=self.blobClient)
        
        openai.api_base = os.environ['AZURE_OPENAI_ENDPOINT']
        openai.api_key = os.environ['AZURE_OPENAI_API_KEY']
        openai.api_version = '2023-05-15'
        openai.api_type = 'azure'

        self.embeddingEngine = OpenAIEmbeddings(deployment=os.environ['AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME'], 
                                                chunk_size=1, 
                                                openai_api_key=os.environ['AZURE_OPENAI_API_KEY'], 
                                                openai_api_base=os.environ['AZURE_OPENAI_ENDPOINT'], 
                                                openai_api_version='2023-05-15',
                                                openai_api_type='azure')
        
        self.vectorDBClient = SearchIndexClient(os.environ['AZURE_COGNITIVE_SEARCH_ENDPOINT'], AzureKeyCredential(os.environ['AZURE_COGNITIVE_SEARCH_KEY']))

    def display(self, router):

        st.title("BotCraft Studio") 
        if st.button('Back to Dashboard'):
            router.redirect('/')
        st.header('Create a new Bot')

        if 'waitingOnBotCreation' not in st.session_state:
            with st.form("Bot Creation Form"):
                
                botName = st.text_input('Bot Name', key='bot_name', placeholder='Give your bot a name')
                files = st.file_uploader('Upload the documents making up your knowledge base', accept_multiple_files=True, type=['pdf', 'docx', 'doc', 'mp4', 'txt', 'mp3', 'wav'], key='upload_kb')
                
                if st.form_submit_button("Create Bot"):
                    st.session_state['createBotInfo'] = {'botName': botName, 'files': files}
                    st.session_state['waitingOnBotCreation'] = True
                    st.experimental_rerun()
        else:
            with st.spinner("Creating Bot..."):
                statusText = st.empty()
                botId = self.initBot(st.session_state['createBotInfo']['botName'], st.session_state['createBotInfo']['files'], statusText)
            statusText.success("Bot Created!")
            router.redirect(f'/chat/{botId}')

    def initBot(self, botName, files, statusText):
        
        botId = str(uuid4())
        # containerClient.upload_blob(name=f'{botName}-{botId}/id.txt', data=botId, overwrite=True)

        statusText.info("Creating Index...")
        containerClient = self.blobClient.get_container_client(st.session_state['active_user'])
        self.createIndex(botName, botId)
        statusText.empty()                                        
        
        statusText.info("Uploading Files...")
        Parallel(n_jobs=-1)(delayed(self.uploadFile)(botName, botId, file, containerClient) for file in files)
        statusText.empty()

        statusText.info("Extracting Content from Files...")
        texts = Parallel(n_jobs=-1)(delayed(self.extractTextFromFiles)(file) for file in files)
        texts = [{'src': file, 'content': text} for file, text in zip(files, texts)]
        statusText.empty()

        statusText.info("Uploading Text Content...")
        Parallel(n_jobs=-1)(delayed(self.uploadText)(botName, botId, text['src'], text['content'], containerClient) for text in texts)
        statusText.empty()

        statusText.info("Vectorizing and Pushing to Database...")
        Parallel(n_jobs=-1)(delayed(self.vectorizeAndPush)(text['src'], text['content']) for text in texts)
        statusText.empty()

        return f'{botName}-{botId}'


    def createIndex(self, botName, botId):
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True, sortable=True, filterable=True, facetable=True),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SearchField(name="content_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), searchable=True, vector_search_dimensions=1536, vector_search_configuration='my-vector-config'),
            SearchableField(name="metadata", type=SearchFieldDataType.String)
        ]
        vectorSearch = VectorSearch(
            algorithm_configurations=[
                HnswVectorSearchAlgorithmConfiguration(
                    name="my-vector-config",
                    parameters={
                        'm': 4,
                        'efConstruction': 400,
                        'efSearch': 500,
                        'metric': 'cosine'
                    }
                )
            ]
        )
        indexName = f'{botName}-{botId}'.lower()
        index = SearchIndex(name=indexName, fields=fields, vector_search=vectorSearch)
        self.vectorDBClient.create_index(index)
        self.vectorStore = AzureSearch(azure_search_endpoint=os.environ['AZURE_COGNITIVE_SEARCH_ENDPOINT'],
                                       azure_search_key=os.environ['AZURE_COGNITIVE_SEARCH_KEY'],
                                       index_name=indexName,
                                       embedding_function=self.embeddingEngine.embed_query)

    def uploadFile(self, botName, botId, file, containerClient):
        containerClient.upload_blob(name=f'{botName}-{botId}/{file.name}', data=file, overwrite=True)
    
    def extractTextFromFiles(self, file):
        # Process file to get text
        if file.type in ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            extension = {'application/pdf': 'pdf', 'application/msword': 'doc', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx'}[file.type]
            textContent = self._processDocument(file, extension)
        elif file.type == 'text/plain':
            textContent = self._processPlaintext(file)
        elif file.type == 'video/mp4':
            textContent = self._processVideo(file)
        elif file.type in ['audio/mpeg', 'audio/wav']:
            textContent = self._processAudio(file)
        elif file.type == 'text/plain':
            textContent = self._processText(file)

        return textContent
    
    def uploadText(self, botName, botId, src, content, containerClient):
        for i, document in enumerate(content):
            textFileName = f"{botName}-{botId}/{src.name}_{i}.txt"
            containerClient.upload_blob(name=textFileName, data=document, overwrite=True)

    def vectorizeAndPush(self, src, content):

        for i, docStr in enumerate(content):
            print("="*30)
            print("***Doc String***")
            print(docStr)
            doc = [Document(page_content=docStr, metadata={'source': f"{src.name}_{i}"})]
            print("="*30)
            print("***Langchain doc object***")
            print(doc)
            print("="*30)
            textSplitter = TokenTextSplitter(chunk_size=500, chunk_overlap=50)
            subDocs = textSplitter.split_documents(doc)
            print(subDocs)
            self.vectorStore.add_documents(subDocs)

    def _processPlaintext(self, file):
        extractedText = file.read().decode()
        cleanedText = cleantext.clean(extractedText, clean_all=False, extra_spaces=True, stemming=False, stopwords=False, lowercase=False, numbers=False, punct=False, reg='\n', reg_replace=' ')
        return [cleanedText]

    def _processDocument(self, file, extension):

        with TempFilePath(file) as tempFilePath:       
            extractedText = textract.process(tempFilePath, extension=extension, encoding='ascii').decode()

        cleanedText = cleantext.clean(extractedText, clean_all=False, extra_spaces=True, stemming=False, stopwords=False, lowercase=False, numbers=False, punct=False, reg='\n', reg_replace=' ')
        return [cleanedText]
    
    def _processVideo(self, videoFile):
        return self.mediaHandler.mediaToTranscript(videoFile, src = 'video')

    def _processAudio(self, audioFile):
        return self.mediaHandler.mediaToTranscript(audioFile, src = 'audio')
