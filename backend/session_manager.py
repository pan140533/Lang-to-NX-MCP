"""
会话管理模块
负责管理用户的建模会话，跟踪零件文件和特征列表
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel


class FeatureData(BaseModel):
    """特征数据模型"""
    feature_id: str
    type: str  # "block", "cylinder", "sphere" 等
    parameters: Dict  # 几何参数
    position: Dict  # 位置信息
    boolean_op: str  # "create", "unite", "subtract", "intersect"
    order: int  # 创建顺序
    nx_object_name: Optional[str] = None  # NX 中的对象名称，如 "BLOCK(0)"
    nx_body_tag: Optional[int] = None  # NX Body Tag（更可靠的标识）
    bounding_box: Optional[Dict] = None  # 边界框缓存


class SessionData(BaseModel):
    """会话数据模型"""
    session_id: str
    part_file: Optional[str] = None  # .prt 文件路径
    features: List[FeatureData] = []
    created_at: str
    last_active: str


class SessionManager:
    """会话管理器"""
    
    def __init__(self, storage_dir: str = "sessions"):
        self.storage_dir = storage_dir
        self.sessions: Dict[str, SessionData] = {}
        
        # 确保存储目录存在
        os.makedirs(storage_dir, exist_ok=True)
        
        # 加载已有会话
        self._load_sessions()
    
    def create_session(self) -> SessionData:
        """创建新会话"""
        import uuid
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        
        session = SessionData(
            session_id=session_id,
            created_at=now,
            last_active=now
        )
        
        self.sessions[session_id] = session
        self._save_session(session)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """获取会话"""
        session = self.sessions.get(session_id)
        if session:
            # 更新最后活动时间
            session.last_active = datetime.now().isoformat()
            self._save_session(session)
        return session
    
    def add_feature(self, session_id: str, feature: FeatureData) -> bool:
        """向会话添加特征"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.features.append(feature)
        self._save_session(session)
        return True
    
    def get_features(self, session_id: str) -> List[FeatureData]:
        """获取会话的所有特征"""
        session = self.get_session(session_id)
        return session.features if session else []
    
    def set_part_file(self, session_id: str, part_file: str) -> bool:
        """设置会话的零件文件路径"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.part_file = part_file
        self._save_session(session)
        return True
    
    def delete_feature(self, session_id: str, feature_id: str) -> bool:
        """删除指定特征"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.features = [f for f in session.features if f.feature_id != feature_id]
        self._save_session(session)
        return True
    
    def clear_session(self, session_id: str) -> bool:
        """清空会话（开始新零件）"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.features = []
        session.part_file = None
        self._save_session(session)
        return True
    
    def _save_session(self, session: SessionData):
        """保存会话到文件"""
        file_path = os.path.join(self.storage_dir, f"{session.session_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session.model_dump(), f, ensure_ascii=False, indent=2)
        
        # 同时更新内存中的会话
        self.sessions[session.session_id] = session
    
    def _load_sessions(self):
        """从文件加载所有会话"""
        if not os.path.exists(self.storage_dir):
            return
        
        for filename in os.listdir(self.storage_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.storage_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        session = SessionData(**data)
                        self.sessions[session.session_id] = session
                except Exception as e:
                    print(f"加载会话失败 {filename}: {e}")
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """清理超时的会话"""
        from datetime import timedelta
        
        now = datetime.now()
        to_delete = []
        
        for session_id, session in self.sessions.items():
            last_active = datetime.fromisoformat(session.last_active)
            age = now - last_active
            
            if age > timedelta(hours=max_age_hours):
                to_delete.append(session_id)
        
        for session_id in to_delete:
            file_path = os.path.join(self.storage_dir, f"{session_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
            del self.sessions[session_id]
        
        return len(to_delete)
