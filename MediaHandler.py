import requests
import os
import time
import json
import swagger_client
from typing import List, Dict
import tempfile
from uuid import uuid4
from pydub import AudioSegment
from azure.storage.blob import BlobServiceClient

class MediaHandler:
    def __init__(self, blobClient = None):
        self.blobClient = blobClient if blobClient is not None else BlobServiceClient.from_connection_string(os.environ['BLOB_STORAGE_CONNECTION_STRING'])
        self.speechServiceKey = os.environ["SPEECH_KEY"]
        self.speechServiceRegion = os.environ["SPEECH_REGION"]
        
    def setAudioParameters(audioFile: object)->object:
        """
        The Batch transcription of Azure Speech Service requires the audio file to be a 16kHz frame rate mono audio file
        """
        audioFile.set_channels(1)
        audioFile.set_frame_rate(16000)
        return audioFile
    
    def chunkAudioIntoIntervals(audio: object, intervalLength: int = 60)->list:
        """
        Chunks the input audio into equal intervals of the duration intervalLength.
        The intervalLength is the duration of each file in seconds.
        """
        intervalLengthMs = intervalLength*1000
        startTime = 0
        audioSegments = []

        while startTime < len(audio):
            endTime = startTime + intervalLengthMs            
            curSegment = audio[startTime:endTime] if endTime < len(audio) else audio[startTime:]
            audioSegments.append(curSegment)
            startTime = endTime            
        return audioSegments
        
    def extractAudioFromVideo(self, videoFile: object):
        audio = AudioSegment.from_file(videoFile, format = 'mp4')
        return audio
    
    def videoToTranscript(self, videoFile: object, intervalLength = 60):
        audio = self.extractAudioFromVideo(videoFile)
        return self.audioToTranscript(audio, intervalLength)
    
    def audioToTranscript(self, audioFile: object, intervalLength = 60):
        audio = self.setAudioParameters(audioFile)
        chunkedAudioSegments = self.chunkAudioIntoIntervals(audio, intervalLength)
        
        # Create a temporary container with a uuid name and upload all the chunks there for the batch transcription task
        tempContainerName = str(uuid4())
        tempContainerClient = self.blobClient.create_container(tempContainerName)
        
        # Upload the chunks one by one with proper naming
        for index, audioChunk in enumerate(chunkedAudioSegments):
            blobName = f"Minute{index}_to_Minute{index+1}.wav"
            blobClient = tempContainerClient.get_blob_client(blobName)
            with tempfile.NamedTemporaryFile(delete=True) as tempFile:
                audioChunk.export(tempFile, format = 'wav')
                # Get the full path of the temporary file
                tempFilePath = tempFile.name
                with open(tempFilePath, "rb") as data:
                    blobClient.upload_blob(data)
        
        tempContainerUri = tempContainerClient.url
        # Perform Speech to text Batch transcription
        transcriptionJson = self.transcribe(recordingsBlobContainerUri = tempContainerUri, name = f"{audioFile.name}_Transcription", description = f"Transcription of {audioFile.name} chunked into lengths of duartion {intervalLength} seconds.")
        transcriptionOfChunks = self.postProcessTranscriptionResults(originalAudioFileName = os.path.basename(audioFile.name), transcriptions = transcriptionJson)
        # Delete the temporary client
        tempContainerClient.delete_container()
        return transcriptionOfChunks
        
    def postProcessTranscriptionResults(self, originalAudioFileName: str, transcriptions: List[Dict[str, dict]]) -> List[str]:
        textOfAudioChunks = []
        for transcription in transcriptions:
            chunkName = transcription["AudioFileName"]
            header = f"This is the transcription of {originalAudioFileName} for its duration of {chunkName}"
            transcriptionText = transcription["Transcription"]["combinedRecognizedPhrases"][0]["display"]
            chunkText = f"{header}\n\n{transcriptionText}"
            textOfAudioChunks.append(chunkText)
        return textOfAudioChunks            
            
    def transcribe(self, recordingsBlobContainerUri, name, description):
        # configure API key authorization: subscription_key
        configuration = swagger_client.Configuration()
        configuration.api_key["Ocp-Apim-Subscription-Key"] = self.speechServiceKey
        configuration.host = f"https://{self.speechServiceRegion}.api.cognitive.microsoft.com/speechtotext/v3.1"
        
        # create the client object and authenticate
        client = swagger_client.ApiClient(configuration)
        # create an instance of the transcription api class
        api = swagger_client.CustomSpeechTranscriptionsApi(api_client=client)
        # Specify transcription properties by passing a dict to the properties parameter. See
        # https://learn.microsoft.com/azure/cognitive-services/speech-service/batch-transcription-create?pivots=rest-api#request-configuration-options
        # for supported parameters.
        properties = swagger_client.TranscriptionProperties()
        properties.word_level_timestamps_enabled = True
        properties.display_form_word_level_timestamps_enabled = True
        properties.punctuation_mode = "DictatedAndAutomatic"
        properties.profanity_filter_mode = "Masked"
        properties.time_to_live = "PT1H"
        properties.diarization_enabled = True
        properties.diarization = swagger_client.DiarizationProperties(
            swagger_client.DiarizationSpeakersProperties(min_count=1, max_count=5))
        
        transcriptionDefinition = self.transcribeFromContainer(recordingsBlobContainerUri, properties, name, description)        
        createdTranscription, status, headers = api.transcriptions_create_with_http_info(transcription=transcriptionDefinition)

        # get the transcription Id from the location URI
        transcriptionId = headers["location"].split("/")[-1]
        completed = False
        while not completed:
            # wait for 5 seconds before refreshing the transcription status
            time.sleep(5)
            transcription = api.transcriptions_get(transcriptionId)
            # print(f"Transcriptions status: {transcription.status}")
            if transcription.status in ("Failed", "Succeeded"):
                completed = True
            TranscriptionResults = []
            if transcription.status == "Succeeded":
                paginatedFiles = api.transcriptions_list_files(transcriptionId)
                for fileData in self.paginate(api, paginatedFiles):
                    if fileData.kind != "Transcription":
                        continue

                    audioFileName = os.path.basename(fileData.name).strip(".json").strip(".wav")
                    resultsUrl = fileData.links.content_url
                    results = requests.get(resultsUrl)
                    #print(f"Results for {audioFileName}:\n{results.content.decode('utf-8')}")
                    TranscriptionResults.append({"AudioFileName": audioFileName, "Transcription": results})
            elif transcription.status == "Failed":
                print(f"Transcription failed: {transcription.properties.error.message}")

        return TranscriptionResults
        
        
    def transcribeFromContainer(self, uri, properties, name, description):
        """
        Transcribe all files in the container located at `uri` using the settings specified in `properties`
        using the base model for the specified locale.
        """
        transcription_definition = swagger_client.Transcription(
            display_name=name,
            description=description,
            locale="en-US",
            content_container_url=uri,
            properties=properties
        )
        return transcription_definition
    
    def paginate(self, api, paginatedObject):
        """
        The autogenerated client does not support pagination. This function returns a generator over
        all items of the array that the paginated object `paginatedObject` is part of.
        """
        yield from paginatedObject.values
        typeName = type(paginatedObject).__name__
        authSettings = ["api_key"]
        while paginatedObject.next_link:
            link = paginatedObject.next_link[len(api.api_client.configuration.host):]
            paginatedObject, status, headers = api.api_client.call_api(link, "GET",
                response_type=typeName, auth_settings=authSettings)

            if status == 200:
                yield from paginatedObject.values
            else:
                raise Exception(f"could not receive paginated data: status {status}")