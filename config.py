# -*- coding: utf-8 -*-
"""
微博监控系统配置文件

包含系统运行所需的各种配置参数，包括:
- 监控目标配置
- 分析参数配置  
- 输出格式配置
- 系统运行配置
"""

import os
from typing import Dict, List

# ==================== 监控目标配置 ====================

# 目标用户信息
TARGET_USER = "张雷"
TARGET_USER_ID = "1749127163"  # 实际的微博用户ID

# 要监控的微博链接
MONITOR_URLS = [
    "https://weibo.com/7495395256/PwOFabN9D#comment",
    # 可以添加更多特定微博链接
]

# 监控时间配置，暂未实现
MONITOR_SCHEDULE = {
    "hour": 9,        # 每日监控时间（小时）
    "minute": 0,      # 每日监控时间（分钟）
    "timezone": "Asia/Shanghai",  # 时区
}

# ==================== 爬虫配置 ====================
# 浏览器配置
BROWSER_CONFIG = {
    "headless": True,           # 是否无头模式运行
    "window_size": (1920, 1080), # 浏览器窗口大小
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "page_load_timeout": 30,    # 页面加载超时时间（秒）
    "implicit_wait": 10,        # 隐式等待时间（秒）
}

# 抓取配置
SCRAPING_CONFIG = {
    "max_comments_per_post": 200,  # 每条微博最大抓取评论数
    "request_delay": 2,            # 请求间隔（秒）
    "retry_times": 3,              # 重试次数
    "scroll_pause_time": 2,        # 滚动暂停时间（秒）
}

# ==================== 分析配置 ====================
# 问题识别关键词
PROBLEM_KEYWORDS = [
            '问题', '故障', 'bug', 'Bug', 'BUG', '提升',
            '不能', '无法', '失效', '错误', '异常', '不如',
            '卡顿', '死机', '黑屏', '白屏', '闪退', '延迟',
            '电池', '续航', '发热', '充电', '痛点'
            '连接', '蓝牙', 'wifi', 'WiFi', 'WIFI', '不喜欢',
            '建议', '希望', '改进', '优化', '升级', '需求', '更新'
        ]

# 分类关键词
CATEGORY_KEYWORDS = {
            'hardware': ['电池', '屏幕', '按键', '传感器', '充电', '发热', '硬件', '手表', '方表', '圆表'],
            'software': ['系统', '应用', 'app', 'APP', '软件', '程序', '算法'],
            'ui': ['界面', '显示', '菜单', '图标', 'UI', 'ui', '布局', '字体'],
            'feature': ['功能', '特性', '新增', '增加', '支持', '兼容']
        }

SEVERITY_KEYWORDS = {
            'critical': ['死机', '黑屏', '无法开机', '完全无法', '彻底失效'],
            'high': ['严重', '频繁', '经常', '总是', '一直'],
            'medium': ['有时', '偶尔', '间歇', '不稳定'],
            'low': ['建议', '希望', '最好', '可以考虑', '计划']
        }

# 分析参数
ANALYSIS_CONFIG = {
    "similarity_threshold": 0.6,    # 问题相似度阈值
    "min_problem_length": 5,        # 最小问题描述长度
    "max_problem_length": 200,      # 最大问题描述长度
    "frequency_weight": 0.3,        # 频率权重
    "severity_weight": 0.4,         # 严重程度权重
    "engagement_weight": 0.3,       # 互动量权重
}

# ==================== 输出配置 ====================

# 报告配置
REPORT_CONFIG = {
    "max_problems_display": 20,     # 报告中显示的最大问题数
    "max_suggestions": 5,           # 最大建议数
    "include_screenshots": False,   # 是否包含截图
    "enable_password_protection": True,  # 是否启用密码保护
    "report_password": "xiaomi2024",     # 报告访问密码
}

# 文件路径配置
PATH_CONFIG = {
    "reports_dir": "reports",           # 报告保存目录
    "data_dir": "data",                 # 数据保存目录
    "logs_dir": "logs",                 # 日志保存目录
}

# 确保目录存在
for dir_name in PATH_CONFIG.values():
    os.makedirs(dir_name, exist_ok=True)

# ==================== 样式配置 ====================

# 小米品牌色彩配置
XIAOMI_COLORS = {
    "primary": "#FF6700",      # 小米橙
    "secondary": "#333333",   # 深灰
    "background": "#F5F5F5",  # 浅灰背景
    "white": "#FFFFFF",       # 白色
    "danger": "#EF4444",      # 红色（严重问题）
    "warning": "#F59E0B",     # 橙色（警告）
    "info": "#3B82F6",        # 蓝色（信息）
    "success": "#10B981",     # 绿色（成功）
}

# 图表配置
CHART_CONFIG = {
    "severity_colors": {
        "critical": XIAOMI_COLORS["danger"],
        "high": XIAOMI_COLORS["warning"],
        "medium": XIAOMI_COLORS["info"],
        "low": XIAOMI_COLORS["success"]
    },
    "category_colors": {
        "hardware": "#8B5CF6",
        "software": "#06B6D4", 
        "ui": "#84CC16",
        "feature": "#F472B6"
    }
}

# ==================== 系统配置 ====================

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file_handler": True,
    "console_handler": True,
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
}

# 性能配置
PERFORMANCE_CONFIG = {
    "max_concurrent_requests": 3,  # 最大并发请求数
    "cache_enabled": True,         # 是否启用缓存
    "cache_ttl": 3600,            # 缓存有效期（秒）
    "max_memory_usage": 500,      # 最大内存使用（MB）
}

# DeepSeek API配置
USE_LLM_GENERATE = False
DEEPSEEK_CONFIG = {
    "api_base": "https://api.deepseek.com",
    "api_key": "sk-d67f323c7d3a48e39c4f2f8311761894",
    "model": "deepseek-chat",
    "max_tokens": 500,
    "temperature": 0.7,
    "suggestion_prompt": "作为产品经理，请针对以下用户反馈的问题提供技术解决方案。问题分类：{category}，问题描述：{description}。简洁明了，一句话即可，不分点。"
}

# 安全配置
SECURITY_CONFIG = {
    "enable_data_encryption": False,  # 是否启用数据加密
    "anonymize_user_data": True,     # 是否匿名化用户数据
    "max_data_retention_days": 30,   # 数据保留天数
    "enable_audit_log": True,        # 是否启用审计日志
}

# ==================== 辅助函数 ====================

def get_config(section: str, key: str = None):
    """
    获取配置信息
    
    Args:
        section: 配置段名称
        key: 配置键名（可选）
        
    Returns:
        配置值或配置段
    """
    config_map = {
        "target": {
            "user": TARGET_USER,
            "user_id": TARGET_USER_ID,
            "urls": MONITOR_URLS,
            "schedule": MONITOR_SCHEDULE
        },
        "browser": BROWSER_CONFIG,
        "scraping": SCRAPING_CONFIG,
        "analysis": ANALYSIS_CONFIG,
        "report": REPORT_CONFIG,
        "path": PATH_CONFIG,
        "colors": XIAOMI_COLORS,
        "chart": CHART_CONFIG,
        "logging": LOGGING_CONFIG,
        "performance": PERFORMANCE_CONFIG,
        "security": SECURITY_CONFIG
    }
    
    if section not in config_map:
        raise ValueError(f"Unknown config section: {section}")
    
    if key is None:
        return config_map[section]
    
    if key not in config_map[section]:
        raise ValueError(f"Unknown config key: {key} in section: {section}")
    
    return config_map[section][key]

def update_config(section: str, key: str, value):
    """
    更新配置信息
    
    Args:
        section: 配置段名称
        key: 配置键名
        value: 新的配置值
    """
    # 这里可以实现配置的动态更新逻辑
    # 实际项目中可能需要将更新保存到配置文件
    pass

def validate_config():
    """
    验证配置的有效性
    
    Returns:
        bool: 配置是否有效
    """
    try:
        # 检查必要的配置项
        assert TARGET_USER, "TARGET_USER cannot be empty"
        assert TARGET_USER_ID, "TARGET_USER_ID cannot be empty"
        assert MONITOR_URLS, "MONITOR_URLS cannot be empty"
        
        # 检查数值配置的合理性
        assert 0 < ANALYSIS_CONFIG["similarity_threshold"] <= 1, "similarity_threshold must be between 0 and 1"
        assert ANALYSIS_CONFIG["min_problem_length"] > 0, "min_problem_length must be positive"
        assert SCRAPING_CONFIG["max_comments_per_post"] > 0, "max_comments_per_post must be positive"
        
        return True
    except AssertionError as e:
        print(f"Configuration validation failed: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during configuration validation: {e}")
        return False

if __name__ == "__main__":
    # 配置验证
    if validate_config():
        print("Configuration validation passed")
    else:
        print("Configuration validation failed")
    
    # 打印配置信息
    print(f"Target User: {TARGET_USER}")
    print(f"Monitor URLs: {len(MONITOR_URLS)} URLs configured")
    print(f"Report Password: {REPORT_CONFIG['report_password']}")