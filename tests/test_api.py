"""
API 端点单元测试
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app


class TestAPIEndpoints(unittest.TestCase):
    """测试 API 端点"""
    
    def setUp(self):
        """测试前准备"""
        self.client = TestClient(app)
    
    def test_create_session(self):
        """测试创建会话端点"""
        response = self.client.post("/api/session/new")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["status"], "success")
        self.assertIn("session_id", data)
        self.assertTrue(data["session_id"].startswith("sess_"))
        self.assertEqual(data["message"], "新会话已创建")
    
    @patch('main.llm_parser')
    @patch('main.subprocess.run')
    def test_execute_command_create_block(self, mock_subprocess, mock_parser):
        """测试执行创建块命令"""
        # Mock LLM 解析结果
        mock_command = Mock()
        mock_command.command_type = "add_feature"
        mock_command.feature_type = "block"
        mock_command.block = Mock(length=200, width=150, height=100)
        mock_command.cylinder = None
        mock_command.boolean_op = "create"
        mock_command.position = None
        
        mock_parser.parse_command.return_value = mock_command
        
        # Mock subprocess 执行结果
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        # 发送请求
        response = self.client.post(
            "/api/command",
            json={"description": "创建一个长200宽150高100的块"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["status"], "success")
        self.assertIn("session_id", data)
        self.assertIn("features", data)
        self.assertEqual(len(data["features"]), 1)
        self.assertEqual(data["features"][0]["type"], "block")
    
    @patch('main.llm_parser')
    def test_execute_command_query(self, mock_parser):
        """测试查询命令"""
        # 先创建会话并添加特征
        response1 = self.client.post("/api/session/new")
        session_id = response1.json()["session_id"]
        
        # Mock 查询命令
        mock_command = Mock()
        mock_command.command_type = "query"
        mock_parser.parse_command.return_value = mock_command
        
        # 发送查询请求
        response = self.client.post(
            "/api/command",
            json={
                "session_id": session_id,
                "description": "显示当前特征"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["status"], "success")
        self.assertIn("features", data)
    
    @patch('main.llm_parser')
    def test_execute_command_new_part(self, mock_parser):
        """测试新建零件命令"""
        # 先创建会话
        response1 = self.client.post("/api/session/new")
        session_id = response1.json()["session_id"]
        
        # Mock 新建零件命令
        mock_command = Mock()
        mock_command.command_type = "new_part"
        mock_parser.parse_command.return_value = mock_command
        
        # 发送新建零件请求
        response = self.client.post(
            "/api/command",
            json={
                "session_id": session_id,
                "description": "新建一个零件"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "已开始新零件")
        self.assertEqual(len(data["features"]), 0)
    
    def test_execute_command_without_session_id(self):
        """测试不提供 session_id 时自动创建会话"""
        with patch('main.llm_parser') as mock_parser, \
             patch('main.subprocess.run') as mock_subprocess:
            
            # Mock LLM 解析结果
            mock_command = Mock()
            mock_command.command_type = "add_feature"
            mock_command.feature_type = "block"
            mock_command.block = Mock(length=200, width=150, height=100)
            mock_command.cylinder = None
            mock_command.boolean_op = "create"
            mock_parser.parse_command.return_value = mock_command
            
            # Mock subprocess
            mock_result = Mock()
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result
            
            # 不提供 session_id
            response = self.client.post(
                "/api/command",
                json={"description": "创建一个块"}
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertEqual(data["status"], "success")
            self.assertIn("session_id", data)
    
    def test_get_session_info(self):
        """测试获取会话信息"""
        # 先创建会话
        response1 = self.client.post("/api/session/new")
        session_id = response1.json()["session_id"]
        
        # 获取会话信息
        response = self.client.get(f"/api/session/{session_id}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["status"], "success")
        self.assertIn("session", data)
        self.assertEqual(data["session"]["session_id"], session_id)
    
    def test_get_nonexistent_session(self):
        """测试获取不存在的会话"""
        response = self.client.get("/api/session/nonexistent_id")
        
        self.assertEqual(response.status_code, 404)


class TestAPIIntegration(unittest.TestCase):
    """测试 API 集成场景"""
    
    def setUp(self):
        """测试前准备"""
        self.client = TestClient(app)
    
    @patch('main.llm_parser')
    @patch('main.subprocess.run')
    def test_complete_workflow(self, mock_subprocess, mock_parser):
        """测试完整工作流"""
        # Mock subprocess 总是成功
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        # 1. 创建会话
        response = self.client.post("/api/session/new")
        self.assertEqual(response.status_code, 200)
        session_id = response.json()["session_id"]
        
        # 2. 添加块
        mock_command = Mock()
        mock_command.command_type = "add_feature"
        mock_command.feature_type = "block"
        mock_command.block = Mock(length=200, width=150, height=100)
        mock_command.cylinder = None
        mock_command.boolean_op = "create"
        mock_parser.parse_command.return_value = mock_command
        
        response = self.client.post(
            "/api/command",
            json={
                "session_id": session_id,
                "description": "创建一个块"
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["features"]), 1)
        
        # 3. 添加圆柱（减法）
        mock_command.feature_type = "cylinder"
        mock_command.block = None
        mock_command.cylinder = Mock(diameter=50, height=120)
        mock_command.boolean_op = "subtract"
        
        response = self.client.post(
            "/api/command",
            json={
                "session_id": session_id,
                "description": "挖一个孔"
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["features"]), 2)
        
        # 4. 查询特征
        mock_command.command_type = "query"
        
        response = self.client.post(
            "/api/command",
            json={
                "session_id": session_id,
                "description": "显示特征"
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["features"]), 2)
        
        # 5. 新建零件
        mock_command.command_type = "new_part"
        
        response = self.client.post(
            "/api/command",
            json={
                "session_id": session_id,
                "description": "新建零件"
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["features"]), 0)


if __name__ == '__main__':
    unittest.main()
