# pages/向量库浏览.py
import streamlit as st
from rag.ChromaService import chroma_ini
import pandas as pd

def vector_library_browser():
    st.title("🧩 向量库浏览")
    st.markdown("浏览向量库中所有已加载的文档及其向量数据")
    st.divider()
    
    # 统计信息
    stats = chroma_ini.get_document_stats()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📄 已加载文档", stats.get('loaded_files', 0))
    with col2:
        st.metric("🧩 向量总数", stats.get('total_vectors', 0))
    with col3:
        st.metric("📝 MD5记录", stats.get('md5_records', 0))
    
    st.divider()
    
    # 获取所有文档
    documents = chroma_ini.list_all_documents()
    loaded_docs = [doc for doc in documents if doc['is_loaded']]
    
    if not loaded_docs:
        st.info("📭 向量库为空，请先加载文档")
        return
    
    # 文档选择
    st.subheader("📄 选择文档查看向量")
    
    doc_options = {doc['filename']: doc for doc in loaded_docs}
    selected_filename = st.selectbox(
        "选择文档",
        options=list(doc_options.keys()),
        key="vector_doc_select"
    )
    
    if selected_filename:
        selected_doc = doc_options[selected_filename]
        md5_value = selected_doc['md5']
        
        st.divider()
        
        # 获取向量数据
        try:
            results = chroma_ini.chroma.get(where={"md5": md5_value})
            
            if results and results['ids']:
                total_chunks = len(results['ids'])
                st.info(f"📊 文档 **{selected_filename}** 被切割成 **{total_chunks}** 个向量块")
                
                # 统计信息
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 向量块数", total_chunks)
                with col2:
                    # 计算平均长度
                    total_len = sum(len(doc) for doc in results['documents'])
                    avg_len = total_len // total_chunks if total_chunks > 0 else 0
                    st.metric("📏 平均长度", f"{avg_len} 字符")
                with col3:
                    st.metric("📁 文档大小", f"{selected_doc['size']/1024:.2f} KB")
                
                st.divider()
                
                # 搜索过滤
                search_term = st.text_input(
                    "🔍 搜索向量内容（输入关键词过滤）",
                    placeholder="输入关键词搜索...",
                    key="vector_search"
                )
                
                st.divider()
                
                # 显示每个向量块
                st.subheader("📋 向量块列表")
                
                # 分页显示
                page_size = st.selectbox(
                    "每页显示数量",
                    options=[5, 10, 20, 50],
                    index=1,
                    key="vector_page_size"
                )
                
                # 过滤向量
                filtered_data = []
                for i, (doc_id, doc_content, metadata) in enumerate(
                    zip(results['ids'], results['documents'], results['metadatas'])
                ):
                    if search_term:
                        if search_term.lower() in doc_content.lower():
                            filtered_data.append({
                                'index': i + 1,
                                'id': doc_id,
                                'content': doc_content,
                                'metadata': metadata,
                                'length': len(doc_content)
                            })
                    else:
                        filtered_data.append({
                            'index': i + 1,
                            'id': doc_id,
                            'content': doc_content,
                            'metadata': metadata,
                            'length': len(doc_content)
                        })
                
                if not filtered_data:
                    st.info("🔍 没有匹配的向量块")
                    return
                
                # 显示搜索结果统计
                if search_term:
                    st.success(f"🔍 找到 {len(filtered_data)} 个匹配的向量块")
                
                # 分页
                total_pages = (len(filtered_data) - 1) // page_size + 1
                if total_pages > 1:
                    page = st.number_input(
                        "页码",
                        min_value=1,
                        max_value=total_pages,
                        value=1,
                        key="vector_page"
                    )
                else:
                    page = 1
                
                start_idx = (page - 1) * page_size
                end_idx = min(start_idx + page_size, len(filtered_data))
                
                # 显示当前页的向量块
                for item in filtered_data[start_idx:end_idx]:
                    with st.container():
                        col1, col2 = st.columns([1, 8])
                        with col1:
                            st.markdown(f"**#{item['index']}**")
                        with col2:
                            st.caption(f"ID: `{item['id']}`")
                        
                        st.text_area(
                            f"内容",
                            value=item['content'],
                            height=200,
                            key=f"vector_display_{item['id']}",
                            disabled=True,
                            label_visibility="collapsed"
                        )
                        
                        # 显示元数据
                        with st.expander("📌 查看元数据"):
                            st.json(item['metadata'])
                        
                        st.divider()
                
                # 分页信息
                if total_pages > 1:
                    st.caption(f"第 {page} / {total_pages} 页，共 {len(filtered_data)} 个向量块")
                    
            else:
                st.warning("⚠️ 未找到该文件的向量数据")
                
        except Exception as e:
            st.error(f"❌ 获取向量数据失败: {str(e)}")


# 页面配置
st.set_page_config(
    page_title="向量库浏览",
    page_icon="🧩",
    layout="wide"
)

# 显示页面
vector_library_browser()