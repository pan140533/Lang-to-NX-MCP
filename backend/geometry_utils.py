"""
几何计算工具模块
提供边界框计算和位置解析功能
"""
from typing import Dict, Tuple, Optional


class BoundingBox:
    """边界框数据类"""
    
    def __init__(self, min_x: float, min_y: float, min_z: float, 
                 max_x: float, max_y: float, max_z: float):
        self.min_x = min_x
        self.min_y = min_y
        self.min_z = min_z
        self.max_x = max_x
        self.max_y = max_y
        self.max_z = max_z
    
    @property
    def center(self) -> Tuple[float, float, float]:
        """计算几何中心点"""
        return (
            (self.min_x + self.max_x) / 2,
            (self.min_y + self.max_y) / 2,
            (self.min_z + self.max_z) / 2
        )
    
    @property
    def top(self) -> Tuple[float, float, float]:
        """顶部中心（Z轴最大值）"""
        return (
            (self.min_x + self.max_x) / 2,
            (self.min_y + self.max_y) / 2,
            self.max_z
        )
    
    @property
    def bottom(self) -> Tuple[float, float, float]:
        """底部中心（Z轴最小值）"""
        return (
            (self.min_x + self.max_x) / 2,
            (self.min_y + self.max_y) / 2,
            self.min_z
        )
    
    @property
    def left(self) -> Tuple[float, float, float]:
        """左侧中心（X轴最小值）"""
        return (
            self.min_x,
            (self.min_y + self.max_y) / 2,
            (self.min_z + self.max_z) / 2
        )
    
    @property
    def right(self) -> Tuple[float, float, float]:
        """右侧中心（X轴最大值）"""
        return (
            self.max_x,
            (self.min_y + self.max_y) / 2,
            (self.min_z + self.max_z) / 2
        )
    
    @property
    def front(self) -> Tuple[float, float, float]:
        """前面中心（Y轴最大值）"""
        return (
            (self.min_x + self.max_x) / 2,
            self.max_y,
            (self.min_z + self.max_z) / 2
        )
    
    @property
    def back(self) -> Tuple[float, float, float]:
        """后面中心（Y轴最小值）"""
        return (
            (self.min_x + self.max_x) / 2,
            self.min_y,
            (self.min_z + self.max_z) / 2
        )
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'min_x': self.min_x,
            'min_y': self.min_y,
            'min_z': self.min_z,
            'max_x': self.max_x,
            'max_y': self.max_y,
            'max_z': self.max_z
        }


def calculate_position(
    reference_bbox: BoundingBox,
    location: str,
    offset: Optional[Dict[str, float]] = None
) -> Tuple[float, float, float]:
    """
    根据参考边界框和位置关键词计算目标坐标
    
    Args:
        reference_bbox: 参考特征的边界框
        location: 位置关键词
        offset: 偏移量 {x: 0, y: 0, z: 0}
    
    Returns:
        (x, y, z) 目标坐标
    """
    # 位置映射
    position_map = {
        'center': reference_bbox.center,
        'top': reference_bbox.top,
        'bottom': reference_bbox.bottom,
        'left': reference_bbox.left,
        'right': reference_bbox.right,
        'front': reference_bbox.front,
        'back': reference_bbox.back,
        # 别名
        'top_center': reference_bbox.top,
        'bottom_center': reference_bbox.bottom,
    }
    
    # 获取基础位置
    base_position = position_map.get(location.lower(), reference_bbox.center)
    
    # 应用偏移
    if offset and isinstance(offset, dict):
        return (
            base_position[0] + offset.get('x', 0),
            base_position[1] + offset.get('y', 0),
            base_position[2] + offset.get('z', 0)
        )
    
    return base_position
