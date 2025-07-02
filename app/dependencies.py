from app.core.system import QuantAnalysisSystem

# 全局系统实例
_quant_system = None

def get_quant_system():
    """获取量化分析系统实例（单例模式）"""
    global _quant_system
    if _quant_system is None:
        _quant_system = QuantAnalysisSystem()
    return _quant_system