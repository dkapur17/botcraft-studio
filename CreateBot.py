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
from TextProcessor import TextProcessor


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
        page_icon=":pencil:",
        layout="centered")

        self.blobClient = BlobServiceClient.from_connection_string(os.environ['BLOB_STORAGE_CONNECTION_STRING'])
        self.textProcessor = TextProcessor()
        
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

    def display(self):

        st.title("BotCraft Studio") 
        if st.button('Back to Dashboard'):
            st.session_state['activePage'] = 'dashboard'
            st.experimental_rerun()
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
            del st.session_state['waitingOnBotCreation']
            st.session_state['activeBotId'] = botId
            st.session_state['activePage'] = 'chat'
            st.experimental_rerun()

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
        texts = Parallel(n_jobs=-1)(delayed(self.textProcessor.extractTextFromFiles)(file) for file in files)
        texts = [{'src': file, 'content': text['content'], 'file-type': text['file-type']} for file, text in zip(files, texts)]
        statusText.empty()

        statusText.info("Uploading Text Content...")
        Parallel(n_jobs=-1)(delayed(self.uploadText)(botName, botId, text['src'], text['content'], containerClient) for text in texts)
        statusText.empty()

        statusText.info("Vectorizing and Pushing to Database...")
        Parallel(n_jobs=-1)(delayed(self.vectorizeAndPush)(text['src'], text['content'], text['file-type']) for text in texts)
        statusText.empty()

        return f'{botName}-{botId}'


    def createIndex(self, botName, botId):
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True, sortable=True, filterable=True, facetable=True),
            SearchableField(name="content", type=SearchFieldDataType.String, searchable = True),
            SearchField(name="content_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), searchable=True, vector_search_dimensions=1536, vector_search_configuration='my-vector-config'),
            SearchableField(name="metadata", type=SearchFieldDataType.String, searchable = True),
            SearchableField(name="description", type=SearchFieldDataType.String, searchable = True)
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
        self.vectorStore = AzureSearch(azure_search_endpoint=os.environ['AZURE_COGNITIVE_SEARCH_ENDPOINT'],
                                       azure_search_key=os.environ['AZURE_COGNITIVE_SEARCH_KEY'],
                                       index_name=indexName,
                                       embedding_function=self.embeddingEngine.embed_query,
                                       fields = fields,
                                       vector_search=vectorSearch
                                       )

    def uploadFile(self, botName, botId, file, containerClient):
        containerClient.upload_blob(name=f'{botName}-{botId}/{file.name}', data=file, overwrite=True)
    
    
    def uploadText(self, botName, botId, src, content, containerClient):
        for i, document in enumerate(content):
            textFileName = f"{botName}-{botId}/{src.name}_{i}.txt"
            containerClient.upload_blob(name=textFileName, data=document, overwrite=True)

    def vectorizeAndPush(self, src, content, fileType):

        for i, docStr in enumerate(content):
            print("="*30)
            print("***Doc String***")
            print(docStr)
            if src.name.__contains__(".mp4") or src.name.__contains__(".mp3") or src.name.__contains__(".wav"):
                description = f"Transcription of {src.name} from minute {i} to minute {i+1}."
            else:
                description = f"Text content of {src.name}"
            doc = [Document(page_content=docStr, metadata={'source': src.name, 'file-type': fileType, 'description': description})]
            print("="*30)
            print("***Langchain doc object***")
            print(doc)
            print("="*30)
            textSplitter = TokenTextSplitter(chunk_size=1500, chunk_overlap=200)
            subDocs = textSplitter.split_documents(doc)
            print(subDocs)
            self.vectorStore.add_texts(texts = [document.page_content for document in subDocs], metadatas=[document.metadata for document in subDocs])
