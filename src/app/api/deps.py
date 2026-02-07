from src.app.services.chat import chat_service
from src.app.services.audio import audio_service
from src.app.services.memory import memory_service
from src.app.rag.retriever import vector_store

def get_chat_service():
    return chat_service

def get_audio_service():
    return audio_service

def get_vector_store():
    return vector_store
