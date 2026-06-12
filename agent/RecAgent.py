from langchain.agents import create_agent
import os
import sys
# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.model_factory import chat_model
from tools.agent_tools import *
from utils.config_tool import prompt_config
from agent.tools.middleware import log_befort_mode,monitor_tool
from langchain_core.messages import AIMessage

class RecAgent:
    def __init__(self) -> None:
        self.agent = create_agent(
            model = chat_model , # type: ignore
            tools=[rag_summarize,get_weather,rag_webserch],
            system_prompt=prompt_config['main_prompt'],
            middleware=[monitor_tool,log_befort_mode]
        )

    def exe_stream(self,query:str)  :
        inputs = {"messages": [{"role": "user", "content": query}]}
        previous_content = ""
        
        for chunk in self.agent.stream(input=inputs, stream_mode="updates"): # type: ignore
            # 从 model 节点提取内容
            if 'model' in chunk and 'messages' in chunk['model']:
                messages = chunk['model']['messages']
                if messages:
                    last_msg = messages[-1]
                    if hasattr(last_msg, 'content'):
                        current_content = last_msg.content
                        # 只输出新增的部分（实现流式效果）
                        if len(current_content) > len(previous_content):
                            new_content = current_content[len(previous_content):]
                            if new_content:
                                yield new_content
                                previous_content = current_content

if __name__ == "__main__" :
    agent = RecAgent()
    # agent.exe_stream("2026年6月15日,我想带狗狗在成都玩,帮我规划以下行程.") 
    # input = "2026年6月15日到6月17日三天,期间我想带狗狗在成都玩,帮我规划以下行程."
    input = "狗狗吃了东西呕吐,我该怎么急救?"
    for chunk in agent.exe_stream(input) :
        print(chunk,end="",flush= True)