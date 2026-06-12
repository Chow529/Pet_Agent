import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.ChromaService import chroma_ini
from utils.config_tool import prompt_config
from model.model_factory import chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from rag.SummRag import SummRag

class RagService (object):
    def __init__(self) -> None:

        def print_test(value) :
            print(value.to_string())
            return value
        self.chroma = chroma_ini
        self.retriver = self.chroma.get_retriever()
        self.prompt_txt = prompt_config["rag_summarize_prompt"]
        self.prompt = PromptTemplate.from_template(self.prompt_txt)
        self.model = chat_model
        self.chain = self.prompt | RunnableLambda(print_test) | self.model | StrOutputParser() # type: ignore
        self.summ_model1 = SummRag(prompt_config['report_prompt'])
        self.summ_model2 = SummRag(prompt_config['report_prompt_1'])
        


    def rag_summarize(self,query:str,web_content: str = "") ->str:
        content_doc = self.retriver.invoke(query)

        
        # key_word = self.summ_model1.get_key_words(query)

        fulldoc = ""
        for i, doc in enumerate(content_doc):
            fulldoc += f"参考资料{i+1}:\n{doc.page_content}\n\n"

        # web_content = ""
        # if use_web_search:
        #     try:
        #         from agent.tools.agent_tools import rag_webserch
        #         # 将 query 转换为关键词格式
        #         # print("*"*20,key_word,"*"*20)
        #         web_result = rag_webserch(key_word)
        #         web_content = f"\n【网络搜索结果】\n{web_result}"
        #     except Exception as e:
        #         web_content = "无查询结果"
        #     resp = self.summ_model2.get_key_words(web_content)
            # print("*"*20,resp,"*"*20)

        resp = ""
        if web_content and web_content != "":
            resp = self.summ_model2.get_key_words(web_content)
        else :
            web_content = "无网络参考资料"

        return self.chain.invoke(
            {
                "input": query,
                "doc" : fulldoc,
                "web": resp
            }
        )
    
rag = RagService()
if __name__ == "__main__" :
    reg = RagService()
    res = reg.rag_summarize("狗狗呕吐怎么办?")
    print(f"AI输出:{res}")