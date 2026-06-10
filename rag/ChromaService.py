import os
import sys
from pathlib import Path

# 添加项目根目录到路径（让绝对导入生效）
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.file_tool import get_abs_path
from utils.config_tool import chroma_config
from model.model_factory import embedding_model

from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.file_tool import *

class ChromaService :
    def __init__(self) -> None:
        os.makedirs(get_abs_path(chroma_config['knowledge_dir']),exist_ok = True)

        if not os.path.exists(get_abs_path(chroma_config['md5_txt_dir'])) :
            open(get_abs_path(chroma_config['md5_txt_dir']), "w", encoding="utf-8")

        self.chroma = Chroma(
            collection_name=chroma_config["collection_name"],
            embedding_function= embedding_model,
            persist_directory=chroma_config['knowledge_dir']
        )


        self.spliter = RecursiveCharacterTextSplitter(separators = chroma_config['separators'],
                                                      chunk_size = chroma_config['chunk_size'],
                                                      chunk_overlap = chroma_config['chunk_overlap'],
                                                      length_function = len)


    def get_retriever (self):
        """
        获取链
        """
        return self.chroma.as_retriever(search_kwargs = {'k':chroma_config['k']})
    
    def load_document(self) :
        """
        在数据文件夹内读取文件,将文件存入向量库内
        计算文件的md5值,做去重处理
        """
        listFile = get_file_list(chroma_config['knowledge_doc'],allow_type=tuple(chroma_config['allow_type']))

        for file in listFile :
            md5obj = get_file_md5_hex(file)
            if check_md5(md5obj,chroma_config['md5_txt_dir']) :
                
                if file.lower().endswith('.txt') :
                    content = load_txt(file)
                elif file.lower().endswith('.pdf') :
                    content = load_pdf(file)

                if not content:
                    logger.error("文件内无内容")
                    continue
                else :
                    spliterDoc = self.spliter.split_documents(content)
                    if not spliterDoc :
                        logger.error("存入向量数据失败")
                        continue
                    else :
                        doc_ids = [doc.metadata.get('id', str(i)) for i, doc in enumerate(spliterDoc)]
                        #存入向量库
                        self.chroma.add_documents(spliterDoc,ids = doc_ids)                       

                    if not save_md5(md5obj,chroma_config['md5_txt_dir']) :
                        logger.error("存入md5值失败")   
                        self.chroma.delete(ids=doc_ids)
                        logger.info("已删除本次添加的向量数据")
                    else :
                        logger.info("添加md5以及向量数据库已成功")
  
            else :
                logger.info("已经存在知识库内")
                continue

            
            

chroma_ini = ChromaService()
    

if __name__ == "__main__" :
    chroma_ini.load_document()
    res = chroma_ini.get_retriever().invoke("疾病")
    for r in res :
        print(r.page_content)