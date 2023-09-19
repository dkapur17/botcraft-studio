import streamlit as st
import os
from joblib import Parallel, delayed
from azure.storage.blob import BlobServiceClient
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import AzureSearch
from langchain.text_splitter import TokenTextSplitter
from langchain.docstore.document import Document
from azure.search.documents.indexes.models import SimpleField, SearchableField, SearchField, SearchFieldDataType

from TextProcessor import TextProcessor

class BotSidebar:

    def __init__(self, botId):        
        self.botId = botId
        self.botName = botId.split('||==||')[0]
        self.textProcessor = TextProcessor()
        self.blobClient = BlobServiceClient.from_connection_string(os.environ['BLOB_STORAGE_CONNECTION_STRING'])
        self.embeddingEngine = OpenAIEmbeddings(deployment=os.environ['AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME'], 
                                                chunk_size=1, 
                                                openai_api_key=os.environ['AZURE_OPENAI_API_KEY'], 
                                                openai_api_base=os.environ['AZURE_OPENAI_ENDPOINT'], 
                                                openai_api_version='2023-05-15',
                                                openai_api_type='azure')
        self.fileList = self.getFiles()


    def display(self) -> None:
        with st.sidebar:
            if st.button("Back to Dashboard"):
                del st.session_state[f'{self.botId}_files']
                st.session_state['activePage'] = 'dashboard'
                st.experimental_rerun()
            st.title(self.botName)
            if st.button('Clear Chat'):
                st.session_state[f'{self.botId}_messages'] = []
            
            with st.form(f'{self.botId}_uploader'):
                files = st.file_uploader("Add a file to the Knowledge Base", accept_multiple_files=True, type=['pdf', 'docx', 'doc', 'mp4', 'txt', 'mp3', 'wav'], key='update_kb')
                if st.form_submit_button("Upload"):
                    with st.spinner('Adding Documents to Knowledge Base...'):
                        self.uploadFiles(files)
                        st.experimental_rerun()
            st.subheader("Current Knowledge Base")
            fileListMD = '\n'.join([f'- {file}' for file in self.fileList])
            st.markdown(fileListMD)

    def isOriginalUpload(self, blob):
        if not blob.__contains__(".txt"):
            return True
        elif blob.__contains__(".pdf") or blob.__contains__(".mp4") or blob.__contains__(".mp3") or blob.__contains__(".wav") or blob.__contains__(".docx"):
            return False
        elif blob.count(".txt") == 1:
            return True
        return False
    
    def getFiles(self):
        # TODO: Fetch file list from blob storage

        if f'{self.botId}_files' in st.session_state:
            return st.session_state[f'{self.botId}_files']

        currentUser = st.session_state['active_user']
        userContainerClient = self.blobClient.get_container_client(currentUser)
        allBlobs = userContainerClient.list_blob_names()
        
        relevantBlobs = [blob for blob in allBlobs if blob.startswith(f"{self.botId}/")]
        relevantBlobs = list(set([blob for blob in relevantBlobs if self.isOriginalUpload(blob)]))
        userFiles = [blob.split("/")[-1] for blob in relevantBlobs]
        st.session_state[f'{self.botId}_files'] = userFiles
        return userFiles
    
    def uploadFile(self, botId, file, containerClient):
        print(file)
        file.seek(0)
        containerClient.upload_blob(name=f'{botId}/{file.name}', data=file, overwrite=True)
        
    def uploadText(self, botId, src, content, containerClient):
        for i, document in enumerate(content):
            textFileName = f"{botId}/{src.name}_{i}.txt"
            containerClient.upload_blob(name=textFileName, data=document, overwrite=True)

    def vectorizeAndPush(self, src, content, fileType, vectorStore):
        for i, docStr in enumerate(content):
            if src.name.__contains__(".mp4") or src.name.__contains__(".mp3") or src.name.__contains__(".wav"):
                description = f"Transcription of {src.name} from minute {i} to minute {i+1}."
            else:
                description = f"Text content of {src.name}"
            doc = [Document(page_content=docStr, metadata={'source': src.name, 'file-type': fileType, 'description': description})]
            textSplitter = TokenTextSplitter(chunk_size=500, chunk_overlap=50)
            subDocs = textSplitter.split_documents(doc)
            vectorStore.add_texts(texts = [document.page_content for document in subDocs], metadatas=[document.metadata for document in subDocs])
            
    def uploadFiles(self, files):
        print(files)
        # TODO: Upload new files to storage and index them
        # First convert the file to its corresponding text and upload to blob, then add that text content to the already existing index
        currentUser = st.session_state['active_user']
        userContainerClient = self.blobClient.get_container_client(currentUser)
        Parallel(n_jobs=-1)(delayed(self.uploadFile)(self.botId, file, userContainerClient) for file in files)
        
        texts = Parallel(n_jobs=-1)(delayed(self.textProcessor.extractTextFromFiles)(file) for file in files)
        texts = [{'src': file, 'content': text['content'], 'file-type': text['file-type']} for file, text in zip(files, texts)]
        
        Parallel(n_jobs=-1)(delayed(self.uploadText)(self.botId, text['src'], text['content'], userContainerClient) for text in texts)
        
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True, sortable=True, filterable=True, facetable=True),
            SearchableField(name="content", type=SearchFieldDataType.String, searchable = True),
            SearchField(name="content_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), searchable=True, vector_search_dimensions=1536, vector_search_configuration='my-vector-config'),
            SearchableField(name="metadata", type=SearchFieldDataType.String, searchable = True),
            SearchableField(name="description", type=SearchFieldDataType.String, searchable = True)
        ]
        vectorStore = AzureSearch(azure_search_endpoint=os.environ['AZURE_COGNITIVE_SEARCH_ENDPOINT'],
                                       azure_search_key=os.environ['AZURE_COGNITIVE_SEARCH_KEY'],
                                       index_name=self.botId.split("||==||")[1].lower(),
                                       embedding_function=self.embeddingEngine.embed_query,
                                       fields = fields)
        Parallel(n_jobs=-1)(delayed(self.vectorizeAndPush)(text['src'], text['content'], text['file-type'], vectorStore) for text in texts)

        # New files were uploaded, so we need to remove the cached file list
        del st.session_state[f'{self.botId}_files']
        