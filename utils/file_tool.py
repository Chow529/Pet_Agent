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
import serpapi
import requests

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


# @tool(description="从网上检索资料,入参是由逗号分割的关键词字符串")
def rag_webserch(querys:str) ->str:
    """
    根据关键词搜索网络资料
    
    Args:
        querys: 逗号分割的关键词字符串，例如 "狗狗呕吐,狗狗腹泻,宠物医疗"
    
    Returns:
        搜索结果字符串
    """
    keywords = [kw.strip() for kw in querys.split(',') if kw.strip()]
    
    if not keywords:
        return "未提供有效的搜索关键词"
    
    search_query = " ".join(keywords)
    
    # 你的 API Key
    api_key = "cdc835e69e3f05ca0bbc68e05cfa36573a919313570ed74190d78aabcbb8f4af"
    
    try:
        # 创建客户端
        client = serpapi.Client(api_key=api_key)
        
        # 执行搜索
        results = client.search({
            "engine": "google",
            "q": search_query,
            "hl": "zh-cn",      # 中文
            "gl": "cn",         # 中国地区
            "num": 5            # 返回5条结果
        })
        
        # 提取有机搜索结果
        organic_results = results.get("organic_results", [])
        
        if not organic_results:
            return f"未找到关于「{search_query}」的相关信息"
        
        # 格式化结果
        formatted = f"关于「{search_query}」的搜索结果：\n\n"
        for i, item in enumerate(organic_results[:2], 1):
            
            link = item.get("link", "")
            # print("*"*20,f"link  {link}","*"*20)
            if link:
                formatted += f"{i}. {fetch_with_jina(link)}\n"
            formatted += "\n"
        
        return formatted
        
    except Exception as e:
        return f"搜索失败：{str(e)}"
    
def fetch_with_jina(url: str,max_chars :int = 2000) -> str:
    """使用 Jina Reader 获取网页内容"""
    try:
        reader_url = f"https://r.jina.ai/{url}"
        response = requests.get(reader_url, timeout=15)
        
        if response.status_code != 200:
            logger.error(f"Jina Reader 返回错误: {response.status_code}")
            return ""
        
        content = response.text
        
        # 提取 Markdown 正文（跳过 YAML 头）
        # Jina Reader 返回格式：YAML 头 + 两个换行 + Markdown 内容
        if '---\n' in content:
            parts = content.split('---\n', 2)
            if len(parts) >= 3:
                # 取第三部分（Markdown 内容）
                md_content = parts[2]
            else:
                md_content = content
        else:
            md_content = content
        
        # 清理链接格式 [text](url) -> text
        import re
        clean_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', md_content)
        
        # 移除标题标记
        clean_text = re.sub(r'^#{1,6}\s+', '', clean_text, flags=re.MULTILINE)
        
        # 移除列表标记
        clean_text = re.sub(r'^[\s]*[•\-*]\s+', '', clean_text, flags=re.MULTILINE)
        
        # 限制长度
        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars] + "..."
        
        return clean_text.strip()
        
    except Exception as e:
        logger.error(f"Jina Reader 获取失败: {e}")
        return ""

if __name__ == "__main__" :
    list = load_txt("doc/宠物急诊指南.txt")
    print(list[0].page_content)