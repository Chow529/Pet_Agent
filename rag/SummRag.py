#对文本进行总结的agent
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_tool import prompt_config
from model.model_factory import summ_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda

class SummRag(object):
    def __init__(self,prompt:str) -> None:

        def print_test(v):
            # print(v.to_string())
            return v
        
        self.model = summ_model
        self.prompt_txt = prompt #prompt_config['report_prompt']
        self.prompt = PromptTemplate.from_template(self.prompt_txt)
        self.chain = self.prompt |RunnableLambda(print_test)| self.model | StrOutputParser()  # type: ignore

    def get_key_words(self,quer :str) -> str:
        res = self.chain.invoke({"input":quer})

        return res
    


# if __name__ == "__main__" :
#     model = SummRag()
#     res = model.get_key_words("我想知道一些关于宠物医学的基础知识")
#     print(res)