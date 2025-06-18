# -*- coding: utf-8 -*-
"""
微博监控系统日志管理模块

提供统一的日志记录功能，包括:
- 多级别日志记录
- 文件和控制台输出
- 日志轮转管理
- 性能监控日志
"""

import logging
import logging.handlers
import os
import sys
import time
import functools
from datetime import datetime
from typing import Optional, Dict, Any

from config import get_config, PATH_CONFIG, LOGGING_CONFIG

class WeiboMonitorLogger:
    """
    微博监控系统专用日志管理器
    """
    
    def __init__(self, name: str = "WeiboMonitor"):
        """
        初始化日志管理器
        
        Args:
            name: 日志器名称
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, LOGGING_CONFIG["level"]))
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """
        设置日志处理器
        """
        formatter = logging.Formatter(
            LOGGING_CONFIG["format"]
        )
        
        # 文件处理器
        if LOGGING_CONFIG["file_handler"]:
            log_file = os.path.join(
                PATH_CONFIG["logs_dir"], 
                f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
            )
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=LOGGING_CONFIG["max_file_size"],
                backupCount=LOGGING_CONFIG["backup_count"],
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # 控制台处理器  
        if LOGGING_CONFIG["console_handler"]:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def debug(self, message: str, **kwargs):
        """记录调试信息"""
        self.logger.debug(self._format_message(message, **kwargs))
    
    def info(self, message: str, **kwargs):
        """记录一般信息"""
        self.logger.info(self._format_message(message, **kwargs))
    
    def warning(self, message: str, **kwargs):
        """记录警告信息"""
        self.logger.warning(self._format_message(message, **kwargs))
    
    def error(self, message: str, **kwargs):
        """记录错误信息"""
        self.logger.error(self._format_message(message, **kwargs))
    
    def critical(self, message: str, **kwargs):
        """记录严重错误信息"""
        self.logger.critical(self._format_message(message, **kwargs))
    
    def exception(self, message: str, **kwargs):
        """记录异常信息（包含堆栈跟踪）"""
        self.logger.exception(self._format_message(message, **kwargs))
    
    def _format_message(self, message: str, **kwargs) -> str:
        """
        格式化日志消息
        
        Args:
            message: 基础消息
            **kwargs: 额外的上下文信息
            
        Returns:
            格式化后的消息
        """
        if kwargs:
            context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            return f"{message} | {context}"
        return message

class PerformanceLogger:
    """
    性能监控日志记录器
    """
    
    def __init__(self, logger: WeiboMonitorLogger):
        self.logger = logger
        self._start_times: Dict[str, float] = {}
    
    def start_timer(self, operation: str):
        """
        开始计时
        
        Args:
            operation: 操作名称
        """
        self._start_times[operation] = time.time()
        self.logger.debug(f"Started operation: {operation}")
    
    def end_timer(self, operation: str, **context):
        """
        结束计时并记录性能信息
        
        Args:
            operation: 操作名称
            **context: 额外的上下文信息
        """
        if operation not in self._start_times:
            self.logger.warning(f"Timer not started for operation: {operation}")
            return
        
        duration = time.time() - self._start_times[operation]
        del self._start_times[operation]
        
        self.logger.info(
            f"Operation completed: {operation}",
            duration=f"{duration:.2f}s",
            **context
        )
        
        # 如果操作耗时过长，记录警告
        if duration > 30:  # 30秒阈值
            self.logger.warning(
                f"Slow operation detected: {operation}",
                duration=f"{duration:.2f}s",
                **context
            )

def performance_monitor(operation_name: str = None):
    """
    性能监控装饰器
    
    Args:
        operation_name: 操作名称，默认使用函数名
    
    Returns:
        装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(f"Performance.{func.__module__}")
            perf_logger = PerformanceLogger(logger)
            
            op_name = operation_name or f"{func.__name__}"
            perf_logger.start_timer(op_name)
            
            try:
                result = func(*args, **kwargs)
                perf_logger.end_timer(op_name, status="success")
                return result
            except Exception as e:
                perf_logger.end_timer(op_name, status="error", error=str(e))
                raise
        
        return wrapper
    return decorator

def log_function_call(log_args: bool = True, log_result: bool = False):
    """
    函数调用日志装饰器
    
    Args:
        log_args: 是否记录函数参数
        log_result: 是否记录函数返回值
    
    Returns:
        装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(f"FuncCall.{func.__module__}")
            
            # 记录函数调用
            call_info = {"function": func.__name__}
            if log_args:
                call_info["args"] = str(args) if args else "None"
                call_info["kwargs"] = str(kwargs) if kwargs else "None"
            
            logger.debug("Function called", **call_info)
            
            try:
                result = func(*args, **kwargs)
                
                # 记录函数返回
                return_info = {"function": func.__name__, "status": "success"}
                if log_result:
                    return_info["result"] = str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                
                logger.debug("Function returned", **return_info)
                return result
                
            except Exception as e:
                logger.error(
                    "Function failed",
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
        
        return wrapper
    return decorator

class AuditLogger:
    """
    审计日志记录器
    用于记录重要的系统操作和数据变更
    """
    
    def __init__(self):
        self.logger = WeiboMonitorLogger("Audit")
    
    def log_data_collection(self, source: str, count: int, **context):
        """
        记录数据收集操作
        
        Args:
            source: 数据源
            count: 收集到的数据量
            **context: 额外上下文
        """
        self.logger.info(
            "Data collection completed",
            operation="data_collection",
            source=source,
            count=count,
            timestamp=datetime.now().isoformat(),
            **context
        )
    
    def log_analysis_result(self, problems_found: int, **context):
        """
        记录分析结果
        
        Args:
            problems_found: 发现的问题数量
            **context: 额外上下文
        """
        self.logger.info(
            "Analysis completed",
            operation="problem_analysis",
            problems_found=problems_found,
            timestamp=datetime.now().isoformat(),
            **context
        )
    
    def log_report_generation(self, report_path: str, **context):
        """
        记录报告生成操作
        
        Args:
            report_path: 报告文件路径
            **context: 额外上下文
        """
        self.logger.info(
            "Report generated",
            operation="report_generation",
            report_path=report_path,
            timestamp=datetime.now().isoformat(),
            **context
        )
    
    def log_error_event(self, error_type: str, error_message: str, **context):
        """
        记录错误事件
        
        Args:
            error_type: 错误类型
            error_message: 错误消息
            **context: 额外上下文
        """
        self.logger.error(
            "Error event occurred",
            operation="error_event",
            error_type=error_type,
            error_message=error_message,
            timestamp=datetime.now().isoformat(),
            **context
        )

# 全局日志器实例
_loggers: Dict[str, WeiboMonitorLogger] = {}
_audit_logger: Optional[AuditLogger] = None

def get_logger(name: str = "WeiboMonitor") -> WeiboMonitorLogger:
    """
    获取日志器实例（单例模式）
    
    Args:
        name: 日志器名称
        
    Returns:
        日志器实例
    """
    if name not in _loggers:
        _loggers[name] = WeiboMonitorLogger(name)
    return _loggers[name]

def get_audit_logger() -> AuditLogger:
    """
    获取审计日志器实例（单例模式）
    
    Returns:
        审计日志器实例
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger

def setup_logging():
    """
    初始化日志系统
    """
    # 确保日志目录存在
    os.makedirs(PATH_CONFIG["logs_dir"], exist_ok=True)
    
    # 创建主日志器
    main_logger = get_logger()
    main_logger.info("Logging system initialized")
    
    # 创建审计日志器
    audit_logger = get_audit_logger()
    audit_logger.logger.info("Audit logging system initialized")

def cleanup_old_logs(days: int = 7):
    """
    清理旧日志文件
    
    Args:
        days: 保留天数
    """
    logger = get_logger("LogCleanup")
    logs_dir = PATH_CONFIG["logs_dir"]
    
    if not os.path.exists(logs_dir):
        return
    
    current_time = time.time()
    cutoff_time = current_time - (days * 24 * 60 * 60)
    
    cleaned_count = 0
    for filename in os.listdir(logs_dir):
        if filename.endswith('.log'):
            file_path = os.path.join(logs_dir, filename)
            try:
                if os.path.getmtime(file_path) < cutoff_time:
                    os.remove(file_path)
                    cleaned_count += 1
                    logger.debug(f"Removed old log file: {filename}")
            except Exception as e:
                logger.warning(f"Failed to remove log file {filename}: {e}")
    
    if cleaned_count > 0:
        logger.info(f"Cleaned up {cleaned_count} old log files")

if __name__ == "__main__":
    # 测试日志系统
    setup_logging()
    
    # 测试基本日志功能
    logger = get_logger("Test")
    logger.info("Test message", test_param="test_value")
    logger.warning("Test warning")
    logger.error("Test error")
    
    # 测试性能监控
    @performance_monitor("test_operation")
    def test_function():
        time.sleep(1)
        return "test_result"
    
    test_function()
    
    # 测试审计日志
    audit_logger = get_audit_logger()
    audit_logger.log_data_collection("test_source", 100)
    
    print("Logger test completed")