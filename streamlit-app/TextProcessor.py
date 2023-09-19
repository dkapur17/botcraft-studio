import os
import streamlit as st
import cleantext
import openai
import textract
from azure.storage.blob import BlobServiceClient

from MediaHandler import MediaHandler
from utils import TempFilePath


class TextProcessor:
    def __init__(self):
        self.blobClient = BlobServiceClient.from_connection_string(os.environ['BLOB_STORAGE_CONNECTION_STRING'])
        self.mediaHandler = MediaHandler(blobClient=self.blobClient)
    
    def extractTextFromFiles(self, file):
        file.seek(0)
        # Process file to get text
        if file.type in ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            extension = {'application/pdf': 'pdf', 'application/msword': 'doc', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx'}[file.type]
            textContent = self._processDocument(file, extension)
            fileType = "PDF document"
        elif file.type == 'text/plain':
            textContent = self._processPlaintext(file)
            fileType = "Plain text document"
        elif file.type == 'video/mp4':
            textContent = self._processVideo(file)
            fileType = "Video file"
        elif file.type in ['audio/mpeg', 'audio/wav']:
            textContent = self._processAudio(file)
            fileType = "Audio file"
            
        return {'content': textContent, 'file-type': fileType}
    
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