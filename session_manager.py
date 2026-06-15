# session_manager.py
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path


class Session:
    """单个对话会话"""
    def __init__(self, session_id: str, title: str, created_at: datetime = None):
        self.session_id = session_id
        self.title = title
        self.created_at = created_at or datetime.now()
        self.messages: List[Dict[str, Any]] = []
        self.updated_at = datetime.now()
    
    def add_message(self, role: str, content: str):
        """添加消息"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """获取所有消息"""
        return self.messages
    
    def clear_messages(self):
        """清空消息"""
        self.messages = []
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": self.messages
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Session":
        """从字典创建"""
        session = cls(
            session_id=data["session_id"],
            title=data["title"],
            created_at=datetime.fromisoformat(data["created_at"])
        )
        session.messages = data.get("messages", [])
        session.updated_at = datetime.fromisoformat(data["updated_at"])
        return session


class SessionManager:
    """会话管理器"""
    def __init__(self, storage_file: str = "history/sessions.json"):
        self.storage_file = Path(storage_file)
        
        # 确保 history 目录存在
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.sessions: Dict[str, Session] = {}
        self.current_session_id: str = None
        self._load_sessions()
    
    def _load_sessions(self):
        """从文件加载会话"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for session_data in data.get("sessions", []):
                        session = Session.from_dict(session_data)
                        self.sessions[session.session_id] = session
                    
                    self.current_session_id = data.get("current_session_id")
                    print(f"✅ 加载了 {len(self.sessions)} 个会话")
            except Exception as e:
                print(f"❌ 加载会话失败: {e}")
        else:
            print(f"📁 创建新的会话存储文件: {self.storage_file}")
    
    def _save_sessions(self):
        """保存会话到文件"""
        try:
            # 确保目录存在
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "sessions": [session.to_dict() for session in self.sessions.values()],
                "current_session_id": self.current_session_id
            }
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 保存了 {len(self.sessions)} 个会话")
        except Exception as e:
            print(f"❌ 保存会话失败: {e}")
    
    def create_session(self, title: str = None) -> Session:
        """创建新会话"""
        session_id = str(uuid.uuid4())[:8]
        if not title:
            title = f"对话 {len(self.sessions) + 1}"
        
        session = Session(session_id, title)
        self.sessions[session_id] = session
        self.current_session_id = session_id
        self._save_sessions()
        print(f"✨ 创建新会话: {title} (ID: {session_id})")
        return session
    
    def get_current_session(self) -> Session:
        """获取当前会话"""
        if not self.current_session_id or self.current_session_id not in self.sessions:
            return self.create_session()
        return self.sessions[self.current_session_id]
    
    def switch_session(self, session_id: str) -> Session:
        """切换会话"""
        if session_id in self.sessions:
            self.current_session_id = session_id
            self._save_sessions()
            print(f"🔄 切换到会话: {self.sessions[session_id].title}")
            return self.sessions[session_id]
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self.sessions:
            deleted_title = self.sessions[session_id].title
            del self.sessions[session_id]
            
            # 如果删除的是当前会话，切换到其他会话
            if self.current_session_id == session_id:
                if self.sessions:
                    self.current_session_id = list(self.sessions.keys())[0]
                else:
                    self.current_session_id = None
                    self.create_session()
            
            self._save_sessions()
            print(f"🗑️ 删除会话: {deleted_title}")
            return True
        return False
    
    def rename_session(self, session_id: str, new_title: str) -> bool:
        """重命名会话"""
        if session_id in self.sessions:
            old_title = self.sessions[session_id].title
            self.sessions[session_id].title = new_title
            self._save_sessions()
            print(f"✏️ 重命名: {old_title} → {new_title}")
            return True
        return False
    
    def get_all_sessions(self) -> List[Session]:
        """获取所有会话（按更新时间倒序）"""
        sessions = list(self.sessions.values())
        sessions.sort(key=lambda x: x.updated_at, reverse=True)
        return sessions
    
    def clear_current_messages(self):
        """清空当前会话消息"""
        session = self.get_current_session()
        session.clear_messages()
        self._save_sessions()
        print(f"🧹 清空会话消息: {session.title}")
    
    def get_conversation_history(self, session_id: str = None) -> List[Dict]:
        """
        获取对话历史（用于 Agent 上下文）
        
        Args:
            session_id: 会话ID，默认当前会话
        
        Returns:
            消息列表，适合直接传给 Agent
        """
        if session_id:
            session = self.sessions.get(session_id)
        else:
            session = self.get_current_session()
        
        if not session:
            return []
        
        # 转换为 Agent 需要的格式
        messages = []
        for msg in session.get_messages():
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return messages
    
    def add_message_to_current(self, role: str, content: str):
        """给当前会话添加消息"""
        session = self.get_current_session()
        session.add_message(role, content)
        self._save_sessions()


# 使用示例
if __name__ == "__main__":
    # 测试
    manager = SessionManager()
    
    # 创建新会话
    session = manager.create_session("测试对话")
    
    # 添加消息
    manager.add_message_to_current("user", "你好")
    manager.add_message_to_current("assistant", "你好！有什么可以帮助你的？")
    
    # 获取历史
    history = manager.get_conversation_history()
    print("对话历史:", history)
    
    # 查看所有会话
    for s in manager.get_all_sessions():
        print(f"会话: {s.title}, 消息数: {len(s.messages)}")