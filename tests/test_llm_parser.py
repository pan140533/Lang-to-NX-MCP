"""
LLM 解析器单元测试
"""
import unittest
from unittest.mock import Mock, patch
from llm_parser import LLMParser, FeatureCommand, BlockDimensions, CylinderDimensions, Position


class TestLLMParser(unittest.TestCase):
    """测试 LLMParser 类"""
    
    def setUp(self):
        """测试前准备"""
        # 使用 mock 避免实际调用 LLM API
        self.parser = LLMParser(
            api_key="test_key",
            base_url="https://test.api.com",
            model="test-model"
        )
    
    @patch('llm_parser.ChatOpenAI')
    def test_parse_create_block_command(self, mock_llm):
        """测试解析创建块指令"""
        # Mock LLM 响应
        mock_response = Mock()
        mock_response.content = '''{
            "command_type": "add_feature",
            "feature_type": "block",
            "block": {
                "length": 200,
                "width": 150,
                "height": 100
            },
            "cylinder": null,
            "position": {
                "type": "absolute",
                "x": 0,
                "y": 0,
                "z": 0
            },
            "boolean_op": "create",
            "feature_id_to_delete": null
        }'''
        
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance
        
        # 重新创建 parser 以使用 mock
        parser = LLMParser(
            api_key="test_key",
            base_url="https://test.api.com",
            model="test-model"
        )
        parser.llm = mock_llm_instance
        
        # 解析指令
        command = parser.parse_command("创建一个长200宽150高100的块")
        
        # 验证
        self.assertEqual(command.command_type, "add_feature")
        self.assertEqual(command.feature_type, "block")
        self.assertIsNotNone(command.block)
        self.assertEqual(command.block.length, 200)
        self.assertEqual(command.block.width, 150)
        self.assertEqual(command.block.height, 100)
        self.assertEqual(command.boolean_op, "create")
    
    @patch('llm_parser.ChatOpenAI')
    def test_parse_create_cylinder_command(self, mock_llm):
        """测试解析创建圆柱指令"""
        mock_response = Mock()
        mock_response.content = '''{
            "command_type": "add_feature",
            "feature_type": "cylinder",
            "block": null,
            "cylinder": {
                "diameter": 50,
                "height": 120
            },
            "position": {
                "type": "absolute",
                "x": 0,
                "y": 0,
                "z": 0
            },
            "boolean_op": "create",
            "feature_id_to_delete": null
        }'''
        
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance
        
        parser = LLMParser(
            api_key="test_key",
            base_url="https://test.api.com",
            model="test-model"
        )
        parser.llm = mock_llm_instance
        
        command = parser.parse_command("创建一个直径50高120的圆柱")
        
        self.assertEqual(command.command_type, "add_feature")
        self.assertEqual(command.feature_type, "cylinder")
        self.assertIsNotNone(command.cylinder)
        self.assertEqual(command.cylinder.diameter, 50)
        self.assertEqual(command.cylinder.height, 120)
    
    @patch('llm_parser.ChatOpenAI')
    def test_parse_subtract_command(self, mock_llm):
        """测试解析减法（挖孔）指令"""
        mock_response = Mock()
        mock_response.content = '''{
            "command_type": "add_feature",
            "feature_type": "cylinder",
            "block": null,
            "cylinder": {
                "diameter": 50,
                "height": 120
            },
            "position": {
                "type": "relative",
                "location": "center"
            },
            "boolean_op": "subtract",
            "feature_id_to_delete": null
        }'''
        
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance
        
        parser = LLMParser(
            api_key="test_key",
            base_url="https://test.api.com",
            model="test-model"
        )
        parser.llm = mock_llm_instance
        
        command = parser.parse_command("在块上挖一个直径50高120的圆柱孔")
        
        self.assertEqual(command.command_type, "add_feature")
        self.assertEqual(command.boolean_op, "subtract")
    
    @patch('llm_parser.ChatOpenAI')
    def test_parse_unite_command(self, mock_llm):
        """测试解析并集（合并）指令"""
        mock_response = Mock()
        mock_response.content = '''{
            "command_type": "add_feature",
            "feature_type": "cylinder",
            "block": null,
            "cylinder": {
                "diameter": 60,
                "height": 80
            },
            "position": {
                "type": "absolute",
                "x": 0,
                "y": 0,
                "z": 0
            },
            "boolean_op": "unite",
            "feature_id_to_delete": null
        }'''
        
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance
        
        parser = LLMParser(
            api_key="test_key",
            base_url="https://test.api.com",
            model="test-model"
        )
        parser.llm = mock_llm_instance
        
        command = parser.parse_command("加一个直径60高80的圆柱并合并")
        
        self.assertEqual(command.command_type, "add_feature")
        self.assertEqual(command.boolean_op, "unite")
    
    @patch('llm_parser.ChatOpenAI')
    def test_parse_new_part_command(self, mock_llm):
        """测试解析新建零件指令"""
        mock_response = Mock()
        mock_response.content = '''{
            "command_type": "new_part",
            "feature_type": null,
            "block": null,
            "cylinder": null,
            "position": null,
            "boolean_op": "create",
            "feature_id_to_delete": null
        }'''
        
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance
        
        parser = LLMParser(
            api_key="test_key",
            base_url="https://test.api.com",
            model="test-model"
        )
        parser.llm = mock_llm_instance
        
        command = parser.parse_command("新建一个零件")
        
        self.assertEqual(command.command_type, "new_part")
    
    @patch('llm_parser.ChatOpenAI')
    def test_parse_query_command(self, mock_llm):
        """测试解析查询指令"""
        mock_response = Mock()
        mock_response.content = '''{
            "command_type": "query",
            "feature_type": null,
            "block": null,
            "cylinder": null,
            "position": null,
            "boolean_op": "create",
            "feature_id_to_delete": null
        }'''
        
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance
        
        parser = LLMParser(
            api_key="test_key",
            base_url="https://test.api.com",
            model="test-model"
        )
        parser.llm = mock_llm_instance
        
        command = parser.parse_command("显示当前有哪些特征")
        
        self.assertEqual(command.command_type, "query")
    
    @patch('llm_parser.ChatOpenAI')
    def test_parse_with_context(self, mock_llm):
        """测试带上下文的解析"""
        mock_response = Mock()
        mock_response.content = '''{
            "command_type": "add_feature",
            "feature_type": "cylinder",
            "block": null,
            "cylinder": {
                "diameter": 50,
                "height": 120
            },
            "position": {
                "type": "relative",
                "reference_feature_id": "feat_001",
                "location": "center"
            },
            "boolean_op": "subtract",
            "feature_id_to_delete": null
        }'''
        
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance
        
        parser = LLMParser(
            api_key="test_key",
            base_url="https://test.api.com",
            model="test-model"
        )
        parser.llm = mock_llm_instance
        
        # 提供上下文
        context = [
            {
                "feature_id": "feat_001",
                "type": "block",
                "parameters": {"length": 200, "width": 150, "height": 100}
            }
        ]
        
        command = parser.parse_command("在块上挖一个孔", context=context)
        
        self.assertEqual(command.command_type, "add_feature")
        self.assertEqual(command.boolean_op, "subtract")


class TestDataModels(unittest.TestCase):
    """测试数据模型"""
    
    def test_block_dimensions(self):
        """测试块尺寸模型"""
        block = BlockDimensions(length=200, width=150, height=100)
        
        self.assertEqual(block.length, 200)
        self.assertEqual(block.width, 150)
        self.assertEqual(block.height, 100)
    
    def test_cylinder_dimensions(self):
        """测试圆柱尺寸模型"""
        cylinder = CylinderDimensions(diameter=50, height=120)
        
        self.assertEqual(cylinder.diameter, 50)
        self.assertEqual(cylinder.height, 120)
    
    def test_position_absolute(self):
        """测试绝对位置"""
        position = Position(type="absolute", x=10, y=20, z=30)
        
        self.assertEqual(position.type, "absolute")
        self.assertEqual(position.x, 10)
        self.assertEqual(position.y, 20)
        self.assertEqual(position.z, 30)
    
    def test_position_relative(self):
        """测试相对位置"""
        position = Position(
            type="relative",
            reference_feature_id="feat_001",
            location="center"
        )
        
        self.assertEqual(position.type, "relative")
        self.assertEqual(position.reference_feature_id, "feat_001")
        self.assertEqual(position.location, "center")
    
    def test_feature_command_create(self):
        """测试创建特征命令"""
        command = FeatureCommand(
            command_type="add_feature",
            feature_type="block",
            block=BlockDimensions(length=200, width=150, height=100),
            boolean_op="create"
        )
        
        self.assertEqual(command.command_type, "add_feature")
        self.assertEqual(command.feature_type, "block")
        self.assertEqual(command.boolean_op, "create")
        self.assertIsNotNone(command.block)
    
    def test_feature_command_subtract(self):
        """测试减法命令"""
        command = FeatureCommand(
            command_type="add_feature",
            feature_type="cylinder",
            cylinder=CylinderDimensions(diameter=50, height=120),
            boolean_op="subtract"
        )
        
        self.assertEqual(command.command_type, "add_feature")
        self.assertEqual(command.feature_type, "cylinder")
        self.assertEqual(command.boolean_op, "subtract")
        self.assertIsNotNone(command.cylinder)


if __name__ == '__main__':
    unittest.main()
