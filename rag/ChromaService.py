import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import hashlib
import json

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.file_tool import get_abs_path
from utils.config_tool import chroma_config
from model.model_factory import embedding_model

from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.file_tool import *
from utils.logging_tool import logger

class ChromaService:
    def __init__(self) -> None:
        os.makedirs(get_abs_path(chroma_config['knowledge_dir']), exist_ok=True)
        
        # 创建MD5记录文件和删除记录文件
        md5_path = get_abs_path(chroma_config['md5_txt_dir'])
        if not os.path.exists(md5_path):
            open(md5_path, "w", encoding="utf-8")
        
        

        self.chroma = Chroma(
            collection_name=chroma_config["collection_name"],
            embedding_function=embedding_model,
            persist_directory=chroma_config['knowledge_dir']
        )

        self.spliter = RecursiveCharacterTextSplitter(
            separators=chroma_config['separators'],
            chunk_size=chroma_config['chunk_size'],
            chunk_overlap=chroma_config['chunk_overlap'],
            length_function=len
        )

    def get_retriever(self):
        """获取检索器"""
        return self.chroma.as_retriever(search_kwargs={'k': chroma_config['k']})
    
    # @classmethod
    def load_document_signal(self,fileName:str) -> bool:
        fileName = get_abs_path(fileName)
        if not fileName.lower().endswith((".txt",".pdf")) :
            return False
        else :
            md5obj = get_file_md5_hex(fileName)
            if check_md5(md5obj, chroma_config['md5_txt_dir']):
                if fileName.lower().endswith('.txt'):
                    content = load_txt(fileName)
                elif fileName.lower().endswith('.pdf'):
                    content = load_pdf(fileName)

                if not content:
                    logger.error("文件内无内容")
                else:
                    # 为每个文档添加元数据
                    for doc in content:
                        doc.metadata['source_file'] = os.path.basename(fileName)
                        doc.metadata['file_path'] = fileName
                        doc.metadata['md5'] = md5obj
                        doc.metadata['file_type'] = os.path.splitext(fileName)[1]
                    
                    spliterDoc = self.spliter.split_documents(content)
                    print("长度:",len(spliterDoc))
                    if not spliterDoc:
                        logger.error("文档分割失败")
                    else:
                        # 生成更稳定的ID：使用文件MD5 + 索引
                        doc_ids = [f"{md5obj}_{i}" for i in range(len(spliterDoc))]
                        
                        # 存入向量库
                        try:
                            self.chroma.add_documents(spliterDoc, ids=doc_ids)
                            logger.info(f"成功添加 {len(doc_ids)} 条向量数据")
                        except Exception as e:
                            logger.error(f"存入向量数据库失败: {e}")


                    if not save_md5(md5obj, chroma_config['md5_txt_dir']):
                        logger.error("存入md5值失败")
                        try:
                            self.chroma.delete(ids=doc_ids)
                            logger.info("已删除本次添加的向量数据")
                        except Exception as e:
                            logger.error(f"删除向量数据失败: {e}")
                        return False
                    else:
                        logger.info(f"文件 {os.path.basename(fileName)} 添加成功")
                        return True
            else:
                logger.info(f"文件 {os.path.basename(fileName)} 已经存在于知识库内")
                return False
            
            return False
 

    def load_document(self):
        """
        在数据文件夹内读取文件，将文件存入向量库内
        计算文件的md5值，做去重处理
        """
        listFile = get_file_list(
            chroma_config['knowledge_doc'],
            allow_type=tuple(chroma_config['allow_type'])
        )

        for file in listFile:
            md5obj = get_file_md5_hex(file)
            if check_md5(md5obj, chroma_config['md5_txt_dir']):
                
                if file.lower().endswith('.txt'):
                    content = load_txt(file)
                elif file.lower().endswith('.pdf'):
                    content = load_pdf(file)
                else:
                    logger.warning(f"不支持的文件格式: {file}")
                    continue

                if not content:
                    logger.error("文件内无内容")
                    continue
                else:
                    # 为每个文档添加元数据
                    for doc in content:
                        doc.metadata['source_file'] = os.path.basename(file)
                        doc.metadata['file_path'] = file
                        doc.metadata['md5'] = md5obj
                        doc.metadata['file_type'] = os.path.splitext(file)[1]
                    
                    spliterDoc = self.spliter.split_documents(content)
                    if not spliterDoc:
                        logger.error("文档分割失败")
                        continue
                    else:
                        # 生成更稳定的ID：使用文件MD5 + 索引
                        doc_ids = [f"{md5obj}_{i}" for i in range(len(spliterDoc))]
                        
                        # 存入向量库
                        try:
                            self.chroma.add_documents(spliterDoc, ids=doc_ids)
                            logger.info(f"成功添加 {len(doc_ids)} 条向量数据")
                        except Exception as e:
                            logger.error(f"存入向量数据库失败: {e}")
                            continue

                    if not save_md5(md5obj, chroma_config['md5_txt_dir']):
                        logger.error("存入md5值失败")
                        try:
                            self.chroma.delete(ids=doc_ids)
                            logger.info("已删除本次添加的向量数据")
                        except Exception as e:
                            logger.error(f"删除向量数据失败: {e}")
                    else:
                        logger.info(f"文件 {os.path.basename(file)} 添加成功")
            else:
                logger.info(f"文件 {os.path.basename(file)} 已经存在于知识库内")
                continue


    def delete_document_by_filepath(self, file_path: str) -> bool:
        """
        根据文件路径删除知识库数据
        Args:
            file_path: 文件的完整路径
        Returns:
            bool: 删除是否成功
        """
        try:
            # 1. 计算文件的MD5
            md5_value = get_file_md5_hex(file_path)
            filename = os.path.basename(file_path)
            
            logger.info(f"开始删除文件: {filename}, MD5: {md5_value}")
            
            # 2. 删除Chroma中的向量数据
            deleted_count = self._delete_vectors_by_md5(md5_value)
            
            if deleted_count > 0:
                logger.info(f"从向量库中删除了 {deleted_count} 条数据")
            else:
                logger.warning(f"未找到MD5为 {md5_value} 的向量数据")
            
            # 3. 从MD5记录文件中删除
            md5_removed = self._remove_md5_from_file(md5_value)
            if md5_removed:
                logger.info("MD5记录已删除")
            else:
                logger.warning("MD5记录删除失败或不存在")
            
            # 4. 直接删除原始文件（不再移动到回收站）
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"已删除原始文件: {file_path}")
            else:
                logger.warning(f"原始文件不存在: {file_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"删除失败: {str(e)}")
            return False
    
    def delete_document_by_filename(self, filename: str) -> bool:
        """
        根据文件名删除知识库数据
        """
        knowledge_dir = get_abs_path(chroma_config['knowledge_doc'])
        file_path = os.path.join(knowledge_dir, filename)
        
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return False
        
        return self.delete_document_by_filepath(file_path)
    
    def _delete_vectors_by_md5(self, md5_value: str) -> int:
        """
        根据MD5值删除Chroma中的向量数据
        """
        try:
            # 方法1：使用metadata过滤查询（推荐，如果索引支持）
            try:
                # 获取所有匹配的文档ID
                results = self.chroma.get(
                    where={"md5": md5_value}
                )
                
                if results and results['ids']:
                    ids_to_delete = results['ids']
                    self.chroma.delete(ids=ids_to_delete)
                    return len(ids_to_delete)
                return 0
                
            except Exception as e:
                logger.warning(f"使用metadata查询失败: {e}")
                
                # 方法2：如果metadata查询不支持，遍历所有文档（效率较低）
                all_docs = self.chroma.get()
                ids_to_delete = []
                
                if all_docs and all_docs['ids']:
                    for i, doc_id in enumerate(all_docs['ids']):
                        # 检查ID是否包含MD5（因为我们使用了 md5_index 格式）
                        if doc_id.startswith(f"{md5_value}_"):
                            ids_to_delete.append(doc_id)
                    
                    if ids_to_delete:
                        self.chroma.delete(ids=ids_to_delete)
                        return len(ids_to_delete)
                
                return 0
                
        except Exception as e:
            logger.error(f"删除向量数据失败: {str(e)}")
            return 0
    
    def _remove_md5_from_file(self, md5_value: str) -> bool:
        """
        从MD5记录文件中删除指定的MD5值
        """
        try:
            md5_file_path = get_abs_path(chroma_config['md5_txt_dir'])
            
            # 读取所有MD5值
            with open(md5_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 过滤掉要删除的MD5（去除换行符）
            new_lines = [line for line in lines if line.strip() != md5_value]
            
            # 如果长度没变，说明没有找到要删除的MD5
            if len(new_lines) == len(lines):
                logger.warning(f"MD5值 {md5_value} 不在记录文件中")
                return False
            
            # 写回文件
            with open(md5_file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            return True
            
        except Exception as e:
            logger.error(f"删除MD5记录失败: {str(e)}")
            return False
    
    def delete_all_documents(self) -> bool:
        """
        删除所有知识库数据
        """
        try:
            # 1. 获取所有文档
            documents = self.list_all_documents()
            
            if not documents:
                logger.info("知识库为空")
                return True
            
            # 2. 逐个删除
            success_count = 0
            for doc in documents:
                if doc['is_loaded']:
                    if self.delete_document_by_filepath(doc['filepath']):
                        success_count += 1
            
            logger.info(f"成功删除 {success_count}/{len(documents)} 个文档")
            return success_count == len(documents)
            
        except Exception as e:
            logger.error(f"清空知识库失败: {str(e)}")
            return False
    
    # ChromaService.py - 修复状态判断逻辑

    def list_all_documents(self) -> List[Dict]:
        """
        列出所有已加载的文档及其信息 - 直接读取MD5文件判断状态
        """
        documents = []
        knowledge_dir = get_abs_path(chroma_config['knowledge_doc'])
        
        # 获取所有支持的文件
        if not os.path.exists(knowledge_dir):
            logger.warning(f"知识库目录不存在: {knowledge_dir}")
            return documents
        
        listFile = get_file_list(
            knowledge_dir,
            allow_type=tuple(chroma_config['allow_type'])
        )
        
        # 读取MD5文件中的所有MD5值（一次性读取，提高效率）
        md5_file_path = get_abs_path(chroma_config['md5_txt_dir'])
        md5_set = set()
        if os.path.exists(md5_file_path):
            with open(md5_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    md5_val = line.strip()
                    if md5_val:
                        md5_set.add(md5_val)
        
        logger.info(f"从MD5文件中读取到 {len(md5_set)} 个MD5记录")
        
        for file_path in listFile:
            try:
                md5_value = get_file_md5_hex(file_path)
                filename = os.path.basename(file_path)
                
                # 直接检查MD5是否在记录集合中
                is_loaded = md5_value in md5_set
                
                # 获取Chroma中的向量数量
                vector_count = 0
                if is_loaded:
                    try:
                        # 尝试通过metadata查询
                        results = self.chroma.get(where={"md5": md5_value})
                        if results and results['ids']:
                            vector_count = len(results['ids'])
                        else:
                            # 如果metadata查询失败，尝试通过ID前缀查询
                            all_docs = self.chroma.get()
                            if all_docs and all_docs['ids']:
                                vector_count = sum(1 for doc_id in all_docs['ids'] 
                                                if doc_id.startswith(f"{md5_value}_"))
                    except Exception as e:
                        logger.warning(f"获取向量数量失败 {filename}: {e}")
                        vector_count = -1
                
                documents.append({
                    'filename': filename,
                    'filepath': file_path,
                    'md5': md5_value,
                    'is_loaded': is_loaded,
                    'vector_count': vector_count,
                    'size': os.path.getsize(file_path),
                    'modified': os.path.getmtime(file_path)
                })
                
                logger.debug(f"文件: {filename}, MD5: {md5_value[:16]}..., 已加载: {is_loaded}")
                
            except Exception as e:
                logger.error(f"获取文件信息失败 {file_path}: {e}")
                continue
        
        return documents

    def get_document_stats(self) -> Dict:
        """
        获取知识库统计信息
        """
        try:
            # 获取所有文档
            documents = self.list_all_documents()
            # print(documents)
            # 统计已加载的文件
            loaded_files = [doc for doc in documents if doc['is_loaded']]
           
            loaded_count = len(loaded_files)
            # print(loaded_files,"1212",loaded_count)
            # 统计总向量数
            total_vectors = 0
            for doc in loaded_files:
                if doc['vector_count'] > 0:
                    total_vectors += doc['vector_count']
            
            # 如果向量数为0但已加载文件数大于0，尝试从Chroma直接获取
            if total_vectors == 0 and loaded_count > 0:
                try:
                    all_docs = self.chroma.get()
                    if all_docs and all_docs['ids']:
                        total_vectors = len(all_docs['ids'])
                except Exception as e:
                    logger.warning(f"从Chroma获取向量总数失败: {e}")
            
            # 读取MD5文件记录数
            md5_file_path = get_abs_path(chroma_config['md5_txt_dir'])
            md5_count = 0
            if os.path.exists(md5_file_path):
                with open(md5_file_path, 'r', encoding='utf-8') as f:
                    md5_count = len([line for line in f.readlines() if line.strip()])
            
            stats = {
                'total_files': len(documents),
                'loaded_files': loaded_count,
                'total_vectors': total_vectors,
                'md5_records': md5_count
            }
            
            logger.info(f"统计信息: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                'total_files': 0,
                'loaded_files': 0,
                'total_vectors': 0,
                'md5_records': 0
            }


# 创建全局实例
chroma_ini = ChromaService()


if __name__ == "__main__":
    # 测试删除功能
    chroma_ini.load_document()
    
    # 查看统计信息
    stats = chroma_ini.get_document_stats()
    print("知识库统计:", stats)
    
    # 列出所有文档
    docs = chroma_ini.list_all_documents()
    for doc in docs:
        print(f"📄 {doc['filename']} - 状态: {'已加载' if doc['is_loaded'] else '未加载'}")
    
    # 删除测试（取消注释以测试）
    # chroma_ini.delete_document_by_filename("test.pdf")