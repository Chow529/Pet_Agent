import os
import hashlib
import sys
from pathlib import Path
try:
    from .logging_tool import logger
    from .path_tool import get_abs_path
except ImportError:
    # 相对导入失败，添加项目根目录到路径
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.logging_tool import logger
    from utils.path_tool import get_abs_path
from datetime import datetime
from langchain_core.documents import Document 
from pypdf import PdfReader


"""给定文件名称,自动读取文件并将里面的文字翻译成md5格式,md5本质就是对文件的二进制进行哈希算法不需要拿到里面的内容"""
def get_file_md5_hex(filepath : str) -> str:
    path = filepath
    if not os.path.exists(path) :
        logger.error("没有该文件")
        return ""

    md5Obj = hashlib.md5()
    chunk_size = 4096

    try:
        with open(path,"rb") as f:
            chunk = f.read(chunk_size)
            while chunk :
                md5Obj.update(chunk)
                chunk = f.read(chunk_size)
            md5_hex = md5Obj.hexdigest()
            return md5_hex
    except Exception as e:
        logger.error("计算md5值失败")
        return ""

def check_md5(md5:str,dir :str) -> bool :
    """
    检查md5值是否已经存在 true不存在
    
    :param md5: md5值
    :type md5: str
    :param dir: 说明
    :type dir: 路径
    :return: 说明
    :rtype: bool
    """
    # if not os.path.exists(dir):
    #     open(dir, "w", encoding="utf-8")
    #     return True
    # else:
    dirpath = get_abs_path(dir)
    for line in open(dirpath, "r", encoding="utf-8").readlines():
        if md5 == line.strip():
            return False
    return True


def save_md5(md5_str: str,dir :str) -> bool:
        """
        md5值实时存入,对应向量数据库存入一条md5值在txt里面出现一条,相当于映射关系
        
        :param md5_str: md5数值
        :type md5_str: str
        :param dir: 存储路径
        :type dir: str
        """
        dirpath = get_abs_path(dir)
        with open(dirpath, "a", encoding="utf-8") as f:
            f.write(md5_str + "\n")
            return True
        
        return False

def get_file_list(dir:str,allow_type : tuple[str,...] = (".pdf",".txt") ) -> tuple[str,...] :
    filelist = []
    dirpath = get_abs_path(dir)
    if os.path.isdir(dirpath) :
        for f in os.listdir(dirpath) :
            if f.lower().endswith(allow_type) :
                filelist.append(os.path.join(dirpath,f))

    return tuple(filelist)


def load_pdf(dir :str) :
    
    path = dir
    documents = []
    
    if os.path.isfile(path) and path.lower().endswith(".pdf"):
        try:
            reader = PdfReader(path)
            
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text and text.strip():
                    metadata = {
                        "source": path,
                        "file_name": os.path.basename(path),
                        "file_type": "pdf",
                        "page_number": page_num,
                        "total_pages": len(reader.pages),
                        "file_size": os.path.getsize(path),
                        "modified_time": datetime.fromtimestamp(
                            os.path.getmtime(path)
                        ).isoformat()
                    }
                    
                    # 添加 PDF 自带的元数据（如有）
                    if reader.metadata:
                        for key, value in reader.metadata.items():
                            metadata[f"pdf_{key}"] = value
                    
                    doc = Document(
                        page_content=text,
                        metadata=metadata
                    )
                    documents.append(doc)
                    
        except Exception as e:
            print(f"加载 PDF 文件 {path} 时出错: {e}")
    
    return documents


def load_txt(dir :str) -> list[Document]:
    path = dir
    documents = []
    
    if os.path.isfile(path) and path.lower().endswith(".txt"):
        # 尝试多种编码格式
        content = None
        

        try:
            with open(path, 'r', encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            logger.error("打开文件失败")
        
        if content is None:
            raise ValueError(f"无法解码文件 {path}")
        
        if content.strip():
            metadata = {
                "source": path,
                "file_name": os.path.basename(path),
                "file_type": "txt",
                "file_size": os.path.getsize(path),
                "modified_time": datetime.fromtimestamp(
                    os.path.getmtime(path)
                ).isoformat(),
                "encoding": "utf-8"
            }
            
            doc = Document(
                page_content=content,
                metadata=metadata
            )
            documents.append(doc)
    
    return documents


if __name__ == "__main__" :
    list = load_txt("doc/宠物急诊指南.txt")
    print(list[0].page_content)