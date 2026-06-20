"""
会话管理器单元测试
"""
import unittest
import os
import shutil
import json
from datetime import datetime, timedelta
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from session_manager import SessionManager, SessionData, FeatureData


class TestSessionManager(unittest.TestCase):
    """测试 SessionManager 类"""
    
    def setUp(self):
        """测试前准备"""
        self.test_storage_dir = "test_sessions"
        self.manager = SessionManager(storage_dir=self.test_storage_dir)
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_storage_dir):
            shutil.rmtree(self.test_storage_dir)
    
    def test_create_session(self):
        """测试创建会话"""
        session = self.manager.create_session()
        
        # 验证会话属性
        self.assertIsNotNone(session.session_id)
        self.assertTrue(session.session_id.startswith("sess_"))
        self.assertIsNone(session.part_file)
        self.assertEqual(len(session.features), 0)
        self.assertIsNotNone(session.created_at)
        self.assertIsNotNone(session.last_active)
        
        # 验证会话已保存
        self.assertIn(session.session_id, self.manager.sessions)
    
    def test_get_session(self):
        """测试获取会话"""
        # 创建会话
        session = self.manager.create_session()
        session_id = session.session_id
        
        # 获取会话
        retrieved_session = self.manager.get_session(session_id)
        
        self.assertIsNotNone(retrieved_session)
        self.assertEqual(retrieved_session.session_id, session_id)
    
    def test_get_nonexistent_session(self):
        """测试获取不存在的会话"""
        result = self.manager.get_session("nonexistent_id")
        self.assertIsNone(result)
    
    def test_add_feature(self):
        """测试添加特征"""
        session = self.manager.create_session()
        
        feature = FeatureData(
            feature_id="feat_001",
            type="block",
            parameters={"length": 200, "width": 150, "height": 100},
            position={"type": "absolute", "x": 0, "y": 0, "z": 0},
            boolean_op="create",
            order=1
        )
        
        result = self.manager.add_feature(session.session_id, feature)
        
        self.assertTrue(result)
        
        # 验证特征已添加
        features = self.manager.get_features(session.session_id)
        self.assertEqual(len(features), 1)
        self.assertEqual(features[0].feature_id, "feat_001")
        self.assertEqual(features[0].type, "block")
    
    def test_add_multiple_features(self):
        """测试添加多个特征"""
        session = self.manager.create_session()
        
        # 添加第一个特征
        feature1 = FeatureData(
            feature_id="feat_001",
            type="block",
            parameters={"length": 200, "width": 150, "height": 100},
            position={"type": "absolute", "x": 0, "y": 0, "z": 0},
            boolean_op="create",
            order=1
        )
        self.manager.add_feature(session.session_id, feature1)
        
        # 添加第二个特征
        feature2 = FeatureData(
            feature_id="feat_002",
            type="cylinder",
            parameters={"diameter": 50, "height": 120},
            position={"type": "absolute", "x": 0, "y": 0, "z": 0},
            boolean_op="subtract",
            order=2
        )
        self.manager.add_feature(session.session_id, feature2)
        
        # 验证
        features = self.manager.get_features(session.session_id)
        self.assertEqual(len(features), 2)
        self.assertEqual(features[0].type, "block")
        self.assertEqual(features[1].type, "cylinder")
        self.assertEqual(features[1].boolean_op, "subtract")
    
    def test_set_part_file(self):
        """测试设置零件文件路径"""
        session = self.manager.create_session()
        part_file = "output/test_part.prt"
        
        result = self.manager.set_part_file(session.session_id, part_file)
        
        self.assertTrue(result)
        
        # 验证
        updated_session = self.manager.get_session(session.session_id)
        self.assertEqual(updated_session.part_file, part_file)
    
    def test_delete_feature(self):
        """测试删除特征"""
        session = self.manager.create_session()
        
        # 添加两个特征
        feature1 = FeatureData(
            feature_id="feat_001",
            type="block",
            parameters={"length": 200, "width": 150, "height": 100},
            position={"type": "absolute", "x": 0, "y": 0, "z": 0},
            boolean_op="create",
            order=1
        )
        feature2 = FeatureData(
            feature_id="feat_002",
            type="cylinder",
            parameters={"diameter": 50, "height": 120},
            position={"type": "absolute", "x": 0, "y": 0, "z": 0},
            boolean_op="subtract",
            order=2
        )
        self.manager.add_feature(session.session_id, feature1)
        self.manager.add_feature(session.session_id, feature2)
        
        # 删除第一个特征
        result = self.manager.delete_feature(session.session_id, "feat_001")
        
        self.assertTrue(result)
        
        # 验证
        features = self.manager.get_features(session.session_id)
        self.assertEqual(len(features), 1)
        self.assertEqual(features[0].feature_id, "feat_002")
    
    def test_clear_session(self):
        """测试清空会话"""
        session = self.manager.create_session()
        
        # 添加特征和设置零件文件
        feature = FeatureData(
            feature_id="feat_001",
            type="block",
            parameters={"length": 200, "width": 150, "height": 100},
            position={"type": "absolute", "x": 0, "y": 0, "z": 0},
            boolean_op="create",
            order=1
        )
        self.manager.add_feature(session.session_id, feature)
        self.manager.set_part_file(session.session_id, "test.prt")
        
        # 清空会话
        result = self.manager.clear_session(session.session_id)
        
        self.assertTrue(result)
        
        # 验证
        updated_session = self.manager.get_session(session.session_id)
        self.assertEqual(len(updated_session.features), 0)
        self.assertIsNone(updated_session.part_file)
    
    def test_session_persistence(self):
        """测试会话持久化"""
        # 创建会话并添加特征
        session = self.manager.create_session()
        feature = FeatureData(
            feature_id="feat_001",
            type="block",
            parameters={"length": 200, "width": 150, "height": 100},
            position={"type": "absolute", "x": 0, "y": 0, "z": 0},
            boolean_op="create",
            order=1
        )
        self.manager.add_feature(session.session_id, feature)
        
        # 创建新的管理器实例（模拟重启）
        new_manager = SessionManager(storage_dir=self.test_storage_dir)
        
        # 验证会话已加载
        loaded_session = new_manager.get_session(session.session_id)
        self.assertIsNotNone(loaded_session)
        self.assertEqual(len(loaded_session.features), 1)
        self.assertEqual(loaded_session.features[0].feature_id, "feat_001")
    
    def test_cleanup_old_sessions(self):
        """测试清理旧会话"""
        # 创建一个会话
        session = self.manager.create_session()
        
        # 手动修改 last_active 为 25 小时前
        session.last_active = (datetime.now() - timedelta(hours=25)).isoformat()
        self.manager._save_session(session)
        
        # 执行清理（24 小时超时）
        deleted_count = self.manager.cleanup_old_sessions(max_age_hours=24)
        
        self.assertEqual(deleted_count, 1)
        
        # 验证会话已删除
        result = self.manager.get_session(session.session_id)
        self.assertIsNone(result)


class TestFeatureData(unittest.TestCase):
    """测试 FeatureData 数据模型"""
    
    def test_feature_creation(self):
        """测试创建特征"""
        feature = FeatureData(
            feature_id="feat_001",
            type="block",
            parameters={"length": 200, "width": 150, "height": 100},
            position={"type": "absolute", "x": 0, "y": 0, "z": 0},
            boolean_op="create",
            order=1
        )
        
        self.assertEqual(feature.feature_id, "feat_001")
        self.assertEqual(feature.type, "block")
        self.assertEqual(feature.boolean_op, "create")
        self.assertEqual(feature.order, 1)
    
    def test_feature_with_nx_object_name(self):
        """测试带 NX 对象名称的特征"""
        feature = FeatureData(
            feature_id="feat_001",
            type="block",
            parameters={"length": 200, "width": 150, "height": 100},
            position={"type": "absolute", "x": 0, "y": 0, "z": 0},
            boolean_op="create",
            order=1,
            nx_object_name="BLOCK(0)"
        )
        
        self.assertEqual(feature.nx_object_name, "BLOCK(0)")


class TestSessionData(unittest.TestCase):
    """测试 SessionData 数据模型"""
    
    def test_session_creation(self):
        """测试创建会话"""
        now = datetime.now().isoformat()
        session = SessionData(
            session_id="sess_test123",
            created_at=now,
            last_active=now
        )
        
        self.assertEqual(session.session_id, "sess_test123")
        self.assertIsNone(session.part_file)
        self.assertEqual(len(session.features), 0)
    
    def test_session_with_features(self):
        """测试带特征的会话"""
        now = datetime.now().isoformat()
        feature = FeatureData(
            feature_id="feat_001",
            type="block",
            parameters={"length": 200, "width": 150, "height": 100},
            position={"type": "absolute", "x": 0, "y": 0, "z": 0},
            boolean_op="create",
            order=1
        )
        
        session = SessionData(
            session_id="sess_test123",
            part_file="test.prt",
            features=[feature],
            created_at=now,
            last_active=now
        )
        
        self.assertEqual(session.part_file, "test.prt")
        self.assertEqual(len(session.features), 1)
        self.assertEqual(session.features[0].type, "block")


if __name__ == '__main__':
    unittest.main()
