import yaml
from .path_tool import get_abs_path

def load_rag_config(rag_path :str = get_abs_path("config/rag.yml") , encode :str = "utf-8"):
    with open(rag_path,"r",encoding= encode) as f:
        return yaml.load(f,Loader=yaml.FullLoader)
    

def load_chroma_config(chroma_path :str = get_abs_path("config/chroma.yml"), encode :str = "utf-8"):
    with open(chroma_path,"r",encoding= encode) as f:
        return yaml.load(f,Loader=yaml.FullLoader)
    

def load_prompt_config(prompt_path :str = get_abs_path("config/prompt.yml"), encode :str = "utf-8"):
    with open(prompt_path,"r",encoding= encode) as f:
        return yaml.load(f,Loader=yaml.FullLoader)
    
# def load_agent_config(agent_path :str = get_abs_path("config/agent.yml"), encode :str = "utf-8"):
#     with open(agent_path,"r",encoding= encode) as f:
#         return yaml.load(f,Loader=yaml.FullLoader)
    
# def load_public_config(public_path :str = get_abs_path("config/public_config.yml"), encode :str = "utf-8"):
#     with open(public_path,"r",encoding= encode) as f:
#         return yaml.load(f,Loader=yaml.FullLoader)
    

rag_config = load_rag_config()
chroma_config = load_chroma_config()
# agent_config = load_agent_config()
prompt_config = load_prompt_config()
# public_config = load_public_config()

if __name__ == "__main__" :
    print(rag_config["chatmodel_name"])