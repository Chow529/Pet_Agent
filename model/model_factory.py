from abc import ABC,abstractmethod
from typing import Optional
from langchain_openai.chat_models.base import BaseChatOpenAI
from langchain_openai import ChatOpenAI,OpenAIEmbeddings
from langchain_core.embeddings import Embeddings
from utils.config_tool import rag_config
import os

class BaseModelFactory(ABC) :
    @abstractmethod
    def model(self) -> Optional[Embeddings | BaseChatOpenAI] :
        pass


class ChatModelIni(BaseModelFactory) :
    def model(self) -> Optional[None | BaseChatOpenAI] :
        return ChatOpenAI(model = rag_config['chatmodel_name'],
                          base_url=rag_config['base_url'],
                        #   api_key=rag_config['mode_key'])
                          api_key = os.getenv('OPENAI_API_KEY') ) # type: ignore
    

class EmbeddingModeIni(BaseModelFactory):
    def model(self) -> Optional[Embeddings | None] :
        return OpenAIEmbeddings(
                model= rag_config['embeddingmodel_name'],
                # api_key=rag_config['mode_key'],
                api_key = os.getenv('OPENAI_API_KEY') , # type: ignore
                base_url=rag_config["base_url"],
                check_embedding_ctx_length=False
            )
    

chat_model = ChatModelIni().model()
embedding_model = EmbeddingModeIni().model()
summ_model = ChatModelIni().model()