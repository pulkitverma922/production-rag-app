from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Groq (free) — get key at https://console.groq.com
    GROQ_API_KEY: str

    # Pinecone
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str = "rag-index"
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"

    # Chunking
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # Retrieval
    TOP_K: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()