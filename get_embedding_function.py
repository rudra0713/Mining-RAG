import os
from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain_community.embeddings.bedrock import BedrockEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from huggingface_hub import login
from dotenv import load_dotenv
import torch

load_dotenv()

# Log in to Hugging Face Hub
login(token=os.getenv('HUB_TOKEN'))


def get_embedding_function(embedding_type="ollama"):
    """
    Returns an embedding function based on the specified type.
    Options:
        - "ollama_nomic": uses Ollama's nomic-embed-text model (local).
        - "ollama_mxbai": uses Ollama's mxbai-embed-large model (local, larger).
        - "ollama_minilm": uses Ollama's all-MiniLM-L12-v2 model (local, balanced).
        - "openai": uses OpenAI's text-embedding-3-large (cloud-based).
        - "bge_large": uses BAAI/bge-large-en-v1.5 (HuggingFace, local).
        - "e5_large": uses intfloat/e5-large-v2 (HuggingFace, local).
        - "mpnet": uses sentence-transformers/all-mpnet-base-v2 (HuggingFace, local).
        - "bge_m3": uses BAAI/bge-m3 (HuggingFace, local, multilingual, large).
        - "bedrock": uses AWS Bedrock embeddings (cloud-based).
    """
    # Common model kwargs for Hugging Face models
    hf_model_kwargs = {
        "use_auth_token": os.getenv("HF_TOKEN"),
        "device": "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu",
        "trust_remote_code": True
    }

    # Enable quantization for larger models if on GPU
    quantization_config = {
        "load_in_4bit": True
    } if hf_model_kwargs["device"] in ["cuda", "mps"] else None

    if embedding_type == "ollama_nomic":
        return OllamaEmbeddings(model="nomic-embed-text")

    elif embedding_type == "ollama_mxbai":
        return OllamaEmbeddings(model="mxbai-embed-large")

    elif embedding_type == "ollama_minilm":
        return OllamaEmbeddings(model="tazarov/all-minilm-l6-v2-f32")

    elif embedding_type == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found. Did you create a .env file?")
        return OpenAIEmbeddings(model="text-embedding-3-large", api_key=api_key)

    elif embedding_type == "bge_large":
        return HuggingFaceEmbeddings(
            model_name="BAAI/bge-large-en-v1.5",
            cache_folder="./hf_models",
            model_kwargs=hf_model_kwargs
        )

    elif embedding_type == "e5_large":
        return HuggingFaceEmbeddings(
            model_name="intfloat/e5-large-v2",
            cache_folder="./hf_models",
            model_kwargs=hf_model_kwargs
        )

    elif embedding_type == "mpnet":
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",
            cache_folder="./hf_models",
            model_kwargs=hf_model_kwargs
        )

    elif embedding_type == "bge_m3":
        return HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
            cache_folder="./hf_models",
            model_kwargs=hf_model_kwargs,
        )

    elif embedding_type == "bedrock":
        return BedrockEmbeddings(
            credentials_profile_name="default",
            region_name="us-east-1"
        )

    else:
        raise ValueError(f"Unknown embedding type: {embedding_type}")