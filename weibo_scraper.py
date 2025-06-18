#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# deepseek-api-key：sk-d67f323c7d3a48e39c4f2f8311761894
"""
微博监控数据采集脚本
用于自动抓取指定微博账号的评论数据，并生成可视化报告
"""

import os
import json
import time
import datetime
from typing import List, Dict, Any
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import jieba
import jieba.analyse
from collections import Counter
import re
from config import *
from logger import get_logger
from openai import OpenAI

class WeiboMonitor:
    def __init__(self, target_user: str = "雷军"):
        """
        初始化微博监控器
        
        Args:
            target_user: 目标用户名
        """
        self.target_user = target_user
        self.driver = None
        self.comments_data = []
        self.problems_data = []
        
        # 问题关键词定义
        self.problem_keywords = PROBLEM_KEYWORDS
        
        # 严重程度关键词
        self.severity_keywords = SEVERITY_KEYWORDS
        
        # 分类关键词
        self.category_keywords = CATEGORY_KEYWORDS
    
    def setup_driver(self) -> webdriver.Chrome:
        """
        设置Chrome浏览器驱动
        
        Returns:
            配置好的Chrome WebDriver实例
        """
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 无界面模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        return self.driver
    
    def scrape_weibo_comments(self, weibo_url: str, max_comments: int = 100) -> List[Dict]:
        """
        抓取微博评论数据
        
        Args:
            weibo_url: 微博链接
            max_comments: 最大抓取评论数量
            
        Returns:
            评论数据列表
        """
        if not self.driver:
            self.setup_driver()
        
        try:
            self.driver.get(weibo_url)
            time.sleep(3)
            
            # 等待评论区加载
            wait = WebDriverWait(self.driver, 10)
            
            comments = []
            comment_count = 0
            
            # 滚动页面加载更多评论
            while comment_count < max_comments:
                # 查找评论元素
                comment_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.text > span")
                
                for element in comment_elements[comment_count:]:
                    if comment_count >= max_comments:
                        break
                    
                    try:
                        # 提取评论内容
                        # 确保只提取span标签内的文本，排除回复链接
                        comment_text = element.text.strip()
                        
                        # 根据结构，如果存在回复，回复内容在'Comment_associate_text'类中
                        # 确保我们只获取顶层评论，而不是回复
                        # 根据结构，确保只提取纯评论内容，排除回复链接或其他无关文本
                        # 检查是否存在明确的回复标志或者该span元素是回复的一部分
                        # 检查当前评论是否是回复，如果是则跳过
                        # 检查同级或父级元素中是否存在明显的回复标志
                        if element.find_elements(By.XPATH, "./following-sibling::a[contains(@class, 'Comment_associate_text')]" ):
                            continue
                        
                        # 进一步过滤，确保不是转发或包含“回复”关键字的评论
                        if not comment_text or len(comment_text) < 5 or "回复" in comment_text or "//转发了" in comment_text:
                            continue
                        
                        # 提取用户信息 - 基于实际HTML结构
                        try:
                            # 在父容器中查找用户链接
                            user_element = element.find_element(By.XPATH, "../..//a[contains(@class, 'ALink_default_2ibt1')]")
                            username = user_element.text.strip() if user_element.text else "匿名用户"
                            # 如果没有文本内容，尝试从to属性中提取用户名
                            if not username or username == "匿名用户":
                                to_attr = user_element.get_attribute('to')
                                if to_attr and '/u/' in to_attr:
                                    username = to_attr.split('/u/')[-1]
                        except:
                            try:
                                # 备用方案：查找所有用户链接
                                user_elements = element.find_elements(By.XPATH, "../..//a[contains(@href, '/u/')]")
                                if user_elements:
                                    user_element = user_elements[0]
                                    username = user_element.text.strip() if user_element.text else "匿名用户"
                                    if not username or username == "匿名用户":
                                        href = user_element.get_attribute('href')
                                        if href and '/u/' in href:
                                            username = href.split('/u/')[-1].split('?')[0]
                                else:
                                    username = "匿名用户"
                            except:
                                username = "匿名用户"
                        
                        # 提取时间戳 - 基于实际HTML结构
                        try:
                            # 查找评论容器后面的info区域
                            info_container = element.find_element(By.XPATH, "../..//div[contains(@class, 'info')]")
                            # 在info容器中查找包含时间的div
                            time_divs = info_container.find_elements(By.XPATH, ".//div[contains(text(), '-') and contains(text(), ':')]")
                            
                            if time_divs:
                                timestamp_text = time_divs[0].text.strip()
                                # 处理时间格式 "25-5-19 11:00" -> "2025-05-19 11:00:00"
                                if timestamp_text and re.match(r'\d+-\d+-\d+\s+\d+:\d+', timestamp_text):
                                    parts = timestamp_text.split()
                                    if len(parts) >= 2:
                                        date_part = parts[0]  # "25-5-19"
                                        time_part = parts[1]  # "11:00"
                                        
                                        # 转换日期格式
                                        date_nums = date_part.split('-')
                                        if len(date_nums) == 3:
                                            year = '20' + date_nums[0] if len(date_nums[0]) == 2 else date_nums[0]
                                            month = date_nums[1].zfill(2)
                                            day = date_nums[2].zfill(2)
                                            timestamp = f"{year}-{month}-{day} {time_part}:00"
                                        else:
                                            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    else:
                                        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                else:
                                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            else:
                                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            # 备用方案：在整个页面中查找时间信息
                            try:
                                # 根据评论内容查找对应的时间戳
                                time_element = self.driver.find_element(By.XPATH, f"//div[contains(text(), '{comment_text[:20]}')]/ancestor::div[contains(@class, 'Comment_')]/descendant::div[contains(text(), '-') and contains(text(), ':')]")
                                timestamp_text = time_element.text.strip()
                                if timestamp_text and '-' in timestamp_text and ':' in timestamp_text:
                                    timestamp = timestamp_text
                                else:
                                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            except:
                                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        

                        # 提取点赞数 - 基于HTML结构
                        try:
                            # 查找点赞数容器
                            like_element = element.find_element(By.XPATH, "../..//span[contains(@class, 'woo-like-count')]")
                            likes_text = like_element.text.strip()
                            # 处理点赞数格式，可能包含"万"等单位
                            if likes_text:
                                if '万' in likes_text:
                                    likes = int(float(likes_text.replace('万', '')) * 10000)
                                elif 'k' in likes_text.lower():
                                    likes = int(float(likes_text.lower().replace('k', '')) * 1000)
                                else:
                                    likes = int(likes_text) if likes_text.isdigit() else 0
                            else:
                                likes = 0
                        except:
                            try:
                                # 备用方案：查找所有可能的点赞数元素
                                like_elements = element.find_elements(By.XPATH, "../..//span[contains(@class, 'like') or contains(@class, 'count')]")
                                likes = 0
                                for like_elem in like_elements:
                                    text = like_elem.text.strip()
                                    if text and (text.isdigit() or '万' in text or 'k' in text.lower()):
                                        if '万' in text:
                                            likes = int(float(text.replace('万', '')) * 10000)
                                        elif 'k' in text.lower():
                                            likes = int(float(text.lower().replace('k', '')) * 1000)
                                        else:
                                            likes = int(text) if text.isdigit() else 0
                                        break
                            except:
                                likes = 0
                        
                        comment_data = {
                            'id': comment_count + 1,
                            'user': username,
                            'content': comment_text,
                            'timestamp': timestamp,
                            'likes': likes,
                            'screenshot': self.take_screenshot(element)
                        }
                        
                        comments.append(comment_data)
                        comment_count += 1
                        
                    except Exception as e:
                        print(f"提取评论时出错: {e}")
                        continue
                
                # 滚动页面
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # 检查是否还有更多评论
                new_comment_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.text > span")
                if len(new_comment_elements) <= len(comment_elements):
                    break
            
            self.comments_data = comments
            return comments
            
        except Exception as e:
            print(f"抓取评论时发生错误: {e}")
            return []
    
    def take_screenshot(self, element) -> str:
        """
        对指定元素截图并返回base64编码
        
        Args:
            element: 要截图的元素
            
        Returns:
            base64编码的截图数据
        """
        try:
            # 截取元素截图
            screenshot = element.screenshot_as_base64
            return f"data:image/png;base64,{screenshot}"
        except:
            # 如果单个元素截图失败，返回占位图
            return "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjNmNGY2Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzMzMzMzMyIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuaIquWbvuekuuS+izwvdGV4dD48L3N2Zz4="
    
    def analyze_problems(self, comments: List[Dict]) -> List[Dict]:
        """
        分析评论中的问题
        
        Args:
            comments: 评论数据列表
            
        Returns:
            问题数据列表
        """
        problems = []
        problem_id = 1
        
        for comment in comments:
            content = comment['content']
            
            # 检查是否包含问题关键词
            has_problem = any(keyword in content for keyword in self.problem_keywords)
            
            if has_problem:
                # 确定严重程度
                severity = self.determine_severity(content)
                
                # 确定分类
                category = self.determine_category(content)
                
                # 提取关键问题描述
                description = self.extract_problem_description(content)
                
                # 生成改进建议
                suggestion = self.generate_suggestion(content, category)
                
                problem = {
                    'id': problem_id,
                    'description': description,
                    'severity': severity,
                    'category': category,
                    'user': comment['user'],
                    'content': content,
                    'timestamp': comment['timestamp'],
                    'screenshot': comment['screenshot'],
                    'likes': comment['likes'],
                    'frequency': 1,  # 会在后续统计中更新
                    'suggestion': suggestion
                }
                
                problems.append(problem)
                problem_id += 1
        
        # 统计问题频率
        problems = self.calculate_problem_frequency(problems)
        
        self.problems_data = problems
        return problems
    
    def determine_severity(self, content: str) -> str:
        """
        根据内容确定问题严重程度
        
        Args:
            content: 评论内容
            
        Returns:
            严重程度标签
        """
        for severity, keywords in self.severity_keywords.items():
            if any(keyword in content for keyword in keywords):
                return severity
        return 'medium'  # 默认为中等严重程度
    
    def determine_category(self, content: str) -> str:
        """
        根据内容确定问题分类
        
        Args:
            content: 评论内容
            
        Returns:
            问题分类标签
        """
        for category, keywords in self.category_keywords.items():
            if any(keyword in content for keyword in keywords):
                return category
        return 'software'  # 默认为软件问题
    
    def extract_problem_description(self, content: str) -> str:
        """
        从评论中提取问题描述
        
        Args:
            content: 评论内容
            
        Returns:
            问题描述
        """
        # 使用jieba进行关键词提取
        keywords = jieba.analyse.extract_tags(content, topK=5)
        
        # 如果内容较短，直接返回
        if len(content) <= 50:
            return content
        
        # 尝试提取包含问题关键词的句子
        sentences = re.split('[。！？!?]', content)
        for sentence in sentences:
            if any(keyword in sentence for keyword in self.problem_keywords):
                return sentence.strip()
        
        # 如果没有找到，返回前50个字符
        return content[:50] + "..."
    
    def generate_suggestion(self, content: str, category: str) -> str:
        if not USE_LLM_GENERATE:
            return "建议可以调用AI生成"
        
        logger = get_logger("DeepSeekAPI")
        client = OpenAI(
            api_key=DEEPSEEK_CONFIG['api_key'],
            base_url=DEEPSEEK_CONFIG['api_base']
        )
        
        try:
            response = client.chat.completions.create(
                model=DEEPSEEK_CONFIG['model'],
                messages=[{
                    "role": "user",
                    "content": DEEPSEEK_CONFIG['suggestion_prompt'].format(
                        category=category,
                        description=content
                    )
                }],
                max_tokens=DEEPSEEK_CONFIG['max_tokens'],
                temperature=DEEPSEEK_CONFIG['temperature'],
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(
                "DeepSeek API调用失败",
                error=str(e),
                category=category,
                content=content[:100]
            )
            return "建议：已记录该问题，技术团队将尽快分析处理"
    
    def calculate_problem_frequency(self, problems: List[Dict]) -> List[Dict]:
        """
        计算问题出现频率
        
        Args:
            problems: 问题列表
            
        Returns:
            更新频率后的问题列表
        """
        # 根据问题描述相似度合并重复问题
        problem_groups = {}
        
        for problem in problems:
            description = problem['description']
            
            # 简单的相似度检查（可以使用更复杂的算法）
            found_group = False
            for group_key in problem_groups.keys():
                # 检查关键词重叠度
                desc_words = set(jieba.cut(description))
                group_words = set(jieba.cut(group_key))
                
                overlap = len(desc_words & group_words)
                similarity = overlap / max(len(desc_words), len(group_words))
                
                if similarity > 0.6:  # 相似度阈值
                    problem_groups[group_key].append(problem)
                    found_group = True
                    break
            
            if not found_group:
                problem_groups[description] = [problem]
        
        # 更新频率并选择代表性问题
        updated_problems = []
        for group_key, group_problems in problem_groups.items():
            # 选择点赞数最高的作为代表
            representative = max(group_problems, key=lambda x: x['likes'])
            representative['frequency'] = len(group_problems)
            
            # 收集所有用户
            all_users = [p['user'] for p in group_problems]
            representative['affected_users'] = list(set(all_users))
            
            updated_problems.append(representative)
        
        # 按频率和严重程度排序
        severity_weights = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        updated_problems.sort(
            key=lambda x: (severity_weights.get(x['severity'], 0) * 2 + x['frequency']), 
            reverse=True
        )
        
        return updated_problems
    
    def generate_html_report(self, problems: List[Dict], output_path: str = None) -> str:
        """
        生成HTML报告
        
        Args:
            problems: 问题数据列表
            output_path: 输出文件路径
            
        Returns:
            生成的HTML文件路径
        """
        if output_path is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'weibo_monitor_report_{timestamp}.html'
            output_path = os.path.join(PATH_CONFIG['reports_dir'], output_path)
        
        # 统计数据
        total_problems = len(problems)
        total_comments = len(self.comments_data)
        severity_stats = Counter([p['severity'] for p in problems])
        category_stats = Counter([p['category'] for p in problems])
        
        # 读取HTML模板
        template_path = 'complete_report.html'
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
        else:
            # 如果模板不存在，使用简化版本
            html_template = self.get_simple_html_template()
        
        # 准备数据
        report_data = {
            'reportDate': datetime.datetime.now().strftime('%Y年%m月%d日'),
            'targetUser': self.target_user,
            'totalComments': total_comments,
            'totalProblems': total_problems,
            'criticalCount': severity_stats.get('critical', 0),
            'highCount': severity_stats.get('high', 0),
            'mediumCount': severity_stats.get('medium', 0),
            'lowCount': severity_stats.get('low', 0),
            'hardwareCount': category_stats.get('hardware', 0),
            'softwareCount': category_stats.get('software', 0),
            'uiCount': category_stats.get('ui', 0),
            'featureCount': category_stats.get('feature', 0),
            'problems': problems[:20],  # 限制显示前20个问题
            'topSuggestions': problems[:5]  # 前5个建议
        }
        
        # 替换模板中的数据
        html_content = self.replace_template_data(html_template, report_data)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"报告已生成: {output_path}")
        return output_path
    
    def replace_template_data(self, template: str, data: Dict) -> str:
        """
        替换HTML模板中的数据占位符
        
        Args:
            template: HTML模板字符串
            data: 要替换的数据
            
        Returns:
            替换后的HTML字符串
        """
        # 替换JavaScript中的模拟数据
        problems_json = json.dumps(data['problems'], ensure_ascii=False, indent=4)
        
        # 更新统计数据
        replacements = {
            '{{REPORT_DATE}}': data['reportDate'],
            '{{TARGET_USER}}': data['targetUser'],
            '{{TOTAL_COMMENTS}}': str(data['totalComments']),
            '{{TOTAL_PROBLEMS}}': str(data['totalProblems']),
            '{{CRITICAL_COUNT}}': str(data['criticalCount']),
            '{{HIGH_COUNT}}': str(data['highCount']),
            '{{MEDIUM_COUNT}}': str(data['mediumCount']),
            '{{LOW_COUNT}}': str(data['lowCount']),
            '{{HARDWARE_COUNT}}': str(data['hardwareCount']),
            '{{SOFTWARE_COUNT}}': str(data['softwareCount']),
            '{{UI_COUNT}}': str(data['uiCount']),
            '{{FEATURE_COUNT}}': str(data['featureCount'])
        }
        
        result = template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)
        
        # 替换问题数据
        mock_data_pattern = r'const mockProblems = \[.*?\];'
        new_mock_data = f'const mockProblems = {problems_json};'
        result = re.sub(mock_data_pattern, new_mock_data, result, flags=re.DOTALL)
        
        return result
    
    def get_simple_html_template(self) -> str:
        """
        获取简化的HTML模板
        
        Returns:
            简化的HTML模板字符串
        """
        return '''
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>微博监控报告</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { background: #FF6700; color: white; padding: 20px; border-radius: 8px; }
                    .stats { display: flex; gap: 20px; margin: 20px 0; }
                    .stat-card { background: #f5f5f5; padding: 15px; border-radius: 8px; flex: 1; }
                    .problem { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 8px; }
                    .severity-critical { border-left: 5px solid #ef4444; }
                    .severity-high { border-left: 5px solid #f59e0b; }
                    .severity-medium { border-left: 5px solid #3b82f6; }
                    .severity-low { border-left: 5px solid #10b981; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>微博监控报告</h1>
                    <p>监控日期: {{REPORT_DATE}} | 目标用户: {{TARGET_USER}}</p>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <h3>评论总数</h3>
                        <p>{{TOTAL_COMMENTS}}</p>
                    </div>
                    <div class="stat-card">
                        <h3>问题总数</h3>
                        <p>{{TOTAL_PROBLEMS}}</p>
                    </div>
                    <div class="stat-card">
                        <h3>严重问题</h3>
                        <p>{{CRITICAL_COUNT}}</p>
                    </div>
                    <div class="stat-card">
                        <h3>一般问题</h3>
                        <p>{{MEDIUM_COUNT}}</p>
                    </div>
                </div>
                
                <div id="problems-list">
                    <!-- 问题列表将通过JavaScript动态生成 -->
                </div>
                
                <script>
                    const mockProblems = [];
                    // 简化的问题列表渲染
                    function renderProblems() {
                        const container = document.getElementById('problems-list');
                        mockProblems.forEach(problem => {
                            const div = document.createElement('div');
                            div.className = `problem severity-${problem.severity}`;
                            div.innerHTML = `
                                <h3>${problem.description}</h3>
                                <p><strong>分类:</strong> ${problem.category}</p>
                                <p><strong>用户:</strong> ${problem.user}</p>
                                <p><strong>频率:</strong> ${problem.frequency}次</p>
                                <p><strong>建议:</strong> ${problem.suggestion}</p>
                            `;
                            container.appendChild(div);
                        });
                    }
                    
                    document.addEventListener('DOMContentLoaded', renderProblems);
                </script>
            </body>
            </html>
        '''
    
    def run_daily_monitor(self, weibo_urls: List[str]) -> str:
        """
        执行日常监控任务
        
        Args:
            weibo_urls: 要监控的微博链接列表
            
        Returns:
            生成的报告文件路径
        """
        print(f"开始监控 {self.target_user} 的微博...")
        
        all_comments = []
        
        try:
            self.setup_driver()
            
            # 抓取所有指定微博的评论
            for url in weibo_urls:
                print(f"正在抓取: {url}")
                comments = self.scrape_weibo_comments(url)
                all_comments.extend(comments)
                time.sleep(2)  # 避免请求过快
            self.comments_data = all_comments
            
            # 分析问题
            print("正在分析问题...")

            problems = self.analyze_problems(all_comments)
            # 生成报告
            print("正在生成报告...")
            report_path = self.generate_html_report(problems)
            
            # # 保存原始数据
            self.save_raw_data(all_comments, problems)
            
            print(f"监控完成！共发现 {len(problems)} 个问题")
            return report_path
            
        except Exception as e:
            print(f"监控过程中发生错误: {e}")
            return None
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_raw_data(self, comments: List[Dict], problems: List[Dict]):
        """
        保存原始数据到JSON文件
        
        Args:
            comments: 评论数据
            problems: 问题数据
        """
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存评论数据
        save_path = PATH_CONFIG["data_dir"]
        os.makedirs(save_path, exist_ok=True)
        comments_file = os.path.join(save_path,"comments",f'comments_data_{timestamp}.json')
        os.makedirs(os.path.dirname(comments_file), exist_ok=True)
        with open(comments_file, 'w', encoding='utf-8') as f:
            json.dump(comments, f, ensure_ascii=False, indent=2)
        
        # 保存问题数据
        problems_file = os.path.join(save_path,"problems",f'problems_data_{timestamp}.json')
        os.makedirs(os.path.dirname(problems_file), exist_ok=True)
        with open(problems_file, 'w', encoding='utf-8') as f:
            json.dump(problems, f, ensure_ascii=False, indent=2)
        
        print(f"原始数据已保存: {comments_file}, {problems_file}")


def main():
    """
    主函数 - 示例用法
    """
    # 创建监控器实例
    monitor = WeiboMonitor(target_user=TARGET_USER)
    
    # 要监控的微博链接列表（需要根据实际情况更新）
    weibo_urls = MONITOR_URLS
    
    # 运行监控
    report_path = monitor.run_daily_monitor(weibo_urls)
    
    if report_path:
        print(f"\n监控报告已生成: {report_path}")
        print("请使用浏览器打开查看详细报告")
    else:
        print("监控失败，请检查配置和网络连接")


if __name__ == "__main__":
    main()