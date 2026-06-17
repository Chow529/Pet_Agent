# main.py
import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到路径（修正）
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 确保所有子目录都在路径中
sys.path.insert(0, str(PROJECT_ROOT / "agent"))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from session_manager import SessionManager
from agent.RecAgent import RecAgent
from rag.ChromaService import chroma_ini



# 页面配置
st.set_page_config(
    page_title="宠物医疗助手",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS
st.markdown("""
<style>
    /* 聊天消息样式 */
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* 用户消息样式 */
    [data-testid="stChatMessage"][data-testid*="user"] {
        background-color: #e3f2fd;
    }
    
    /* 助手消息样式 */
    [data-testid="stChatMessage"][data-testid*="assistant"] {
        background-color: #f5f5f5;
    }
    
    /* 侧边栏样式 */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* 按钮样式 */
    .stButton button {
        width: 100%;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    /* 删除按钮悬停效果 */
    button[key*="delete_"]:hover {
        background-color: #ff4444;
        color: white;
    }
    
    /* 新对话按钮 */
    button[key="new_chat"] {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    
    button[key="new_chat"]:hover {
        background-color: #45a049;
    }
    
    .upload-container {
        border: 2px dashed #4CAF50;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
            
    .upload-container:hover {
        background-color: #f0f8f0;
    }
            
    /* 隐藏自动生成的导航 */
    .st-emotion-cache-1y4p8pa {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """初始化 session state"""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.session_manager = SessionManager()
        st.session_state.agent = RecAgent()
        st.session_state.current_messages = []
        st.session_state.chroma = chroma_ini


def get_session_manager() -> SessionManager:
    """获取会话管理器"""
    return st.session_state.session_manager


def get_agent() -> RecAgent:
    """获取 Agent"""
    return st.session_state.agent


def save_message(role: str, content: str):
    """保存消息到当前会话"""
    session_manager = get_session_manager()
    session = session_manager.get_current_session()
    session.add_message(role, content)
    session_manager._save_sessions()


def load_current_session_messages():
    """加载当前会话的消息"""
    session_manager = get_session_manager()
    session = session_manager.get_current_session()
    return session.get_messages()


def render_sidebar():
    """渲染侧边栏"""
    session_manager = get_session_manager()
    
    with st.sidebar:
        st.title("🐾 宠物助手")

        # st.page_link("main.py", label="🏠 主界面", icon="🏠")
        # st.page_link("pages/knowledge_manager.py", label="📚 管理知识库", icon="📚")

        st.markdown("---")
        
        # 新对话按钮
        col1, col2  = st.columns([3, 1])
        with col1:
            if st.button("➕ 新对话", key="new_chat", use_container_width=True):
                new_session = session_manager.create_session()
                st.rerun()
        
        with col2:
            if st.button("🗑️ 清空", key="clear_all", use_container_width=True):
                session_manager.clear_current_messages()
                st.rerun()
        

        st.markdown("---")
        st.subheader("📋 历史对话")
        
        # 显示所有对话
        sessions = session_manager.get_all_sessions()
        current_id = session_manager.current_session_id
        
        for session in sessions:
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # 高亮当前对话
                if session.session_id == current_id:
                    button_label = f"📌 **{session.title}**"
                else:
                    # 显示标题和预览
                    preview = ""
                    if session.messages:
                        first_msg = session.messages[0]["content"][:30]
                        preview = f"\n{first_msg}..."
                    button_label = f"💬 {session.title}"
                
                if st.button(button_label, key=f"session_{session.session_id}", use_container_width=True):
                    session_manager.switch_session(session.session_id)
                    st.rerun()
            
            with col2:
                # 删除按钮
                if st.button("❌", key=f"delete_{session.session_id}"):
                    session_manager.delete_session(session.session_id)
                    st.rerun()
        
        st.markdown("---")
        
        # 显示会话统计
        total_messages = sum(len(s.messages) for s in sessions)
        st.caption(f"📊 总计: {len(sessions)} 个对话 | {total_messages} 条消息")


        

def render_chat():
    """渲染聊天区域"""
    session_manager = get_session_manager()
    agent = get_agent()
    current_session = session_manager.get_current_session()
    
    st.title(f"🐕 宠物医疗助手 - {current_session.title}")
    st.caption("专业宠物医疗咨询助手，随时为您解答宠物健康问题")
    
    st.markdown("---")
    
    # 显示聊天历史
    messages = load_current_session_messages()
    
    # 聊天容器
    chat_container = st.container()
    
    with chat_container:
        for msg in messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
    
    # 输入框
    if prompt := st.chat_input("请输入您的问题..."):
        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 保存用户消息
        save_message("user", prompt)
        

        history = load_current_session_messages()

        # 获取 Agent 回复
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                try:
                    # 收集流式输出
                    response_text = ""
                    response_placeholder = st.empty()
                    

                    for chunk in agent.exe_stream(prompt,history[:-1]):
                        response_text += chunk
                        response_placeholder.markdown(response_text + "▌")
                    
                    response_placeholder.markdown(response_text)
                    
                    # 保存助手回复
                    if response_text:
                        save_message("assistant", response_text)
                    
                except Exception as e:
                    error_msg = f"抱歉，处理您的问题时出现错误：{str(e)}"
                    st.error(error_msg)
                    save_message("assistant", error_msg)
        
        st.rerun()




def main():
    init_session_state()
    render_sidebar()
    render_chat()


if __name__ == "__main__":
    main()