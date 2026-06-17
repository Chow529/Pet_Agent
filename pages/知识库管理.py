# pages/知识库管理.py
import streamlit as st
from rag.ChromaService import chroma_ini
from datetime import datetime
import pandas as pd
from utils.file_tool import get_abs_path
import os

def knowledge_base_manager():
    st.subheader("📚 知识库管理")
    
    # 统计信息
    stats = chroma_ini.get_document_stats()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📄 文件总数", stats['total_files'])
    with col2:
        st.metric("✅ 已加载", stats['loaded_files'])
    with col3:
        st.metric("🧩 向量数量", stats['total_vectors'])
    with col4:
        st.metric("📝 MD5记录", stats['md5_records'])
    
    st.divider()
    
    # 操作标签页
    tab1, tab2, tab3 = st.tabs(["📋 文档列表", "🗑️ 删除管理", "📤 上传文档"])
    
    with tab1:
        documents = chroma_ini.list_all_documents()
        
        if not documents:
            st.info("📭 知识库为空")
        else:
            # 显示为表格
            df_data = []
            for doc in documents:
                df_data.append({
                    '文件名': doc['filename'],
                    '状态': '✅ 已加载' if doc['is_loaded'] else '❌ 未加载',
                    '向量数': doc['vector_count'] if doc['vector_count'] >= 0 else 'N/A',
                    '大小(KB)': f"{doc['size']/1024:.2f}",
                    '修改时间': datetime.fromtimestamp(doc['modified']).strftime('%Y-%m-%d %H:%M')
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.divider()
            
            # 加载操作区域
            st.write("### 📚 加载知识库文件")
            
            # 获取所有未加载的文件
            unloaded_docs = [doc for doc in documents if not doc['is_loaded']]
            loaded_docs = [doc for doc in documents if doc['is_loaded']]
            
            # 统计信息
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📄 未加载文件: {len(unloaded_docs)} 个")
            with col2:
                st.success(f"✅ 已加载文件: {len(loaded_docs)} 个")
            
            if not unloaded_docs:
                st.success("🎉 所有文件均已加载！")
            else:
                # 获取所有未加载的文件名列表
                unloaded_filenames = [doc['filename'] for doc in unloaded_docs]
                
                # 使用三列布局：下拉框 + 按钮
                col_select, col_btn = st.columns([4, 1])
                
                with col_select:
                    # 普通 multiselect
                    selected_files = st.multiselect(
                        "选择要加载的文件（可多选）",
                        options=unloaded_filenames,
                        key="load_multiselect",
                        placeholder="请选择要加载的文件..."
                    )
                    
                    # 显示已选择的文件数量
                    if selected_files:
                        st.caption(f"✅ 已选择 {len(selected_files)} 个文件")
                    else:
                        st.caption("💡 提示：从列表中选择要加载的文件")
                
                with col_btn:
                    # 加载按钮放在右侧
                    if st.button("📚 加载选中", type="primary", use_container_width=True, key="load_selected_btn"):
                        if not selected_files:
                            st.warning("⚠️ 请至少选择一个文件")
                        else:
                            success_count = 0
                            fail_count = 0
                            
                            for filename in selected_files:
                                file_path = None
                                for doc in unloaded_docs:
                                    if doc['filename'] == filename:
                                        file_path = doc['filepath']
                                        break
                                
                                if file_path:
                                    with st.spinner(f"正在加载 {filename}..."):
                                        if chroma_ini.load_document_signal(file_path):
                                            success_count += 1
                                        else:
                                            fail_count += 1
                            
                            if success_count > 0:
                                st.success(f"✅ 成功加载 {success_count} 个文件")
                            if fail_count > 0:
                                st.error(f"❌ {fail_count} 个文件加载失败")
                            
                            if success_count > 0:
                                st.rerun()
    
    with tab2:
        documents = chroma_ini.list_all_documents()
        loaded_docs = [doc for doc in documents if doc['is_loaded']]
        unloaded_docs = [doc for doc in documents if not doc['is_loaded']]
        
        if not documents:
            st.info("📭 知识库为空")
        else:
            # 创建子标签页：已加载文件 和 未加载文件
            sub_tab1, sub_tab2 = st.tabs(["✅ 已加载文件", "❌ 未加载文件"])
            
            with sub_tab1:
                if not loaded_docs:
                    st.info("📭 没有已加载的文档")
                else:
                    # 获取已加载的文件名列表
                    loaded_filenames = [doc['filename'] for doc in loaded_docs]
                    
                    # 删除操作区域
                    st.write("### 🗑️ 删除已加载文件")
                    
                    # 统计信息
                    st.info(f"📄 已加载文件: {len(loaded_docs)} 个")
                    
                    # 使用三列布局：下拉框 + 按钮
                    col_select, col_btn = st.columns([4, 1])
                    
                    with col_select:
                        # 普通 multiselect
                        selected_delete = st.multiselect(
                            "选择要删除的已加载文件（可多选）",
                            options=loaded_filenames,
                            key="delete_loaded_multiselect",
                            placeholder="请选择要删除的文件..."
                        )
                        
                        # 显示已选择的文件数量
                        if selected_delete:
                            st.warning(f"⚠️ 已选择 {len(selected_delete)} 个文件，删除后将无法恢复")
                        else:
                            st.caption("💡 提示：从列表中选择要删除的文件")
                    
                    with col_btn:
                        # 删除按钮放在右侧
                        if st.button("🗑️ 删除选中", type="primary", use_container_width=True, key="delete_loaded_btn"):
                            if not selected_delete:
                                st.warning("⚠️ 请至少选择一个文件")
                            else:
                                success_count = 0
                                fail_count = 0
                                
                                for filename in selected_delete:
                                    file_path = None
                                    for doc in loaded_docs:
                                        if doc['filename'] == filename:
                                            file_path = doc['filepath']
                                            break
                                    
                                    if file_path:
                                        with st.spinner(f"正在删除 {filename}..."):
                                            if chroma_ini.delete_document_by_filepath(file_path):
                                                success_count += 1
                                            else:
                                                fail_count += 1
                                
                                if success_count > 0:
                                    st.success(f"✅ 成功删除 {success_count} 个文件")
                                if fail_count > 0:
                                    st.error(f"❌ {fail_count} 个文件删除失败")
                                
                                if success_count > 0:
                                    st.rerun()
            
            with sub_tab2:
                if not unloaded_docs:
                    st.info("📭 没有未加载的文档")
                else:
                    # 获取未加载的文件名列表
                    unloaded_filenames = [doc['filename'] for doc in unloaded_docs]
                    
                    # 删除操作区域
                    st.write("### 🗑️ 删除未加载文件")
                    st.caption("💡 这些文件已上传但尚未加载到知识库，删除后不会影响已加载的数据")
                    
                    # 统计信息
                    st.info(f"📄 未加载文件: {len(unloaded_docs)} 个")
                    
                    # 使用三列布局：下拉框 + 按钮
                    col_select, col_btn = st.columns([4, 1])
                    
                    with col_select:
                        # 普通 multiselect
                        selected_delete_unloaded = st.multiselect(
                            "选择要删除的未加载文件（可多选）",
                            options=unloaded_filenames,
                            key="delete_unloaded_multiselect",
                            placeholder="请选择要删除的文件..."
                        )
                        
                        # 显示已选择的文件数量
                        if selected_delete_unloaded:
                            st.warning(f"⚠️ 已选择 {len(selected_delete_unloaded)} 个未加载文件，将直接从磁盘删除")
                        else:
                            st.caption("💡 提示：从列表中选择要删除的未加载文件")
                    
                    with col_btn:
                        # 删除按钮放在右侧
                        if st.button("🗑️ 删除选中", type="primary", use_container_width=True, key="delete_unloaded_btn"):
                            if not selected_delete_unloaded:
                                st.warning("⚠️ 请至少选择一个文件")
                            else:
                                success_count = 0
                                fail_count = 0
                                
                                for filename in selected_delete_unloaded:
                                    file_path = None
                                    for doc in unloaded_docs:
                                        if doc['filename'] == filename:
                                            file_path = doc['filepath']
                                            break
                                    
                                    if file_path:
                                        with st.spinner(f"正在删除 {filename}..."):
                                            try:
                                                # 直接删除文件，不需要删除向量数据（因为未加载）
                                                if os.path.exists(file_path):
                                                    os.remove(file_path)
                                                    success_count += 1
                                                    st.info(f"✅ 已删除: {filename}")
                                                else:
                                                    st.warning(f"⚠️ 文件不存在: {filename}")
                                                    fail_count += 1
                                            except Exception as e:
                                                st.error(f"❌ 删除失败 {filename}: {str(e)}")
                                                fail_count += 1
                                
                                if success_count > 0:
                                    st.success(f"✅ 成功删除 {success_count} 个未加载文件")
                                if fail_count > 0:
                                    st.error(f"❌ {fail_count} 个文件删除失败")
                                
                                if success_count > 0:
                                    st.rerun()
    
        with tab3:
            st.subheader("📤 上传文档到知识库")
            st.info("💡 选择文件后自动上传，上传成功后请到「📋 文档列表」加载")
            
            # 文件上传
            uploaded_file = st.file_uploader(
                "选择文件上传 (支持 PDF 和 TXT 格式)",
                type=['pdf', 'txt'],
                key="upload_file",
                help="支持单个文件上传，最大 200MB"
            )
            
            if uploaded_file:
                from utils.config_tool import chroma_config
                
                # 生成文件唯一标识（文件名 + 文件大小 + 修改时间）
                file_key = f"{uploaded_file.name}_{uploaded_file.size}"
                
                # 检查是否已经上传过这个文件
                if 'uploaded_keys' not in st.session_state:
                    st.session_state.uploaded_keys = set()
                
                # 如果文件已经上传过，跳过
                if file_key in st.session_state.uploaded_keys:
                    st.info(f"📄 文件 '{uploaded_file.name}' 已上传")
                else:
                    # 保存文件
                    upload_dir = chroma_config['knowledge_doc']
                    os.makedirs(get_abs_path(upload_dir), exist_ok=True)
                    
                    file_path = os.path.join(get_abs_path(upload_dir), uploaded_file.name)
                    
                    # 检查文件是否已存在
                    file_exists = os.path.exists(file_path)
                    
                    # 如果文件已存在，询问是否覆盖
                    if file_exists:
                        overwrite = st.checkbox("覆盖已存在的文件", key="overwrite_checkbox")
                        if not overwrite:
                            st.info("💡 提示：文件已存在，请勾选覆盖或重命名文件")
                            st.stop()
                    
                    # 保存文件
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # 记录已上传的文件
                    st.session_state.uploaded_keys.add(file_key)
                    
                    st.success(f"✅ 文件 '{uploaded_file.name}' 上传成功！请到「📋 文档列表」加载")
                    
                    # 刷新页面，清除上传器状态
                    st.rerun()

st.set_page_config(
    page_title="知识库管理",
    page_icon="📚",
    layout="wide"
)

# 显示知识库管理页面
knowledge_base_manager()