#!/usr/bin/env python3
"""
AI Reference Checker - 查询ChatGPT、Perplexity、Gemini是否引用官网内容
使用requests + BeautifulSoup实现多引擎搜索分析
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import re
from datetime import datetime
from urllib.parse import quote, urlparse, unquote


class AIReferenceChecker:
    """AI引用检测器"""

    def __init__(self, target_urls):
        """
        初始化
        :param target_urls: 目标官网URL列表
        """
        self.target_urls = target_urls
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }

    def search_on_ai_engine(self, engine, query, retries=3):
        """
        在指定AI引擎上搜索（经由DuckDuckGo HTML版检索该引擎域名下的页面）
        DuckDuckGo对连续GET会限流，改用POST表单并做指数退避重试
        :param engine: 引擎名称 ('chatgpt', 'perplexity', 'gemini')
        :param query: 搜索关键词
        :return: 搜索结果HTML
        """
        site_domains = {
            "chatgpt": "chatgpt.com",
            "perplexity": "perplexity.ai",
            "gemini": "gemini.google.com"
        }

        if engine not in site_domains:
            return None

        full_query = f"{query} site:{site_domains[engine]}"

        for attempt in range(retries):
            try:
                response = requests.post(
                    "https://html.duckduckgo.com/html/",
                    data={"q": full_query, "b": ""},
                    headers=self.headers,
                    timeout=15
                )
                response.raise_for_status()
                # 限流时返回的异常页远小于正常结果页（约30KB+）
                if len(response.text) > 20000 or 'result__a' in response.text:
                    return response.text
                print(f"  ⧗ {engine.upper()} 第{attempt + 1}次被限流，退避重试...")
            except Exception as e:
                print(f"  ✗ {engine.upper()} 搜索失败: {e}")
            time.sleep(2 ** attempt + 1)

        print(f"  ✗ {engine.upper()} 重试{retries}次后仍失败，跳过")
        return None

    def extract_snippets(self, html, target_urls):
        """
        从搜索结果中提取与目标URL相关的片段
        :param html: 搜索结果HTML
        :param target_urls: 目标URL列表
        :return: 相关片段列表
        """
        snippets = []
        soup = BeautifulSoup(html, 'html.parser')

        # DuckDuckGo HTML版结果链接在 a.result__a，跳转链接需解码uddg参数
        result_links = soup.select('a.result__a') or soup.find_all('a')

        for element in result_links:
            text = element.get_text(strip=True)
            href = str(element.get('href', ''))

            # 解码 DuckDuckGo 重定向链接
            if 'duckduckgo.com/l/' in href and 'uddg=' in href:
                match = re.search(r'uddg=([^&]+)', href)
                if match:
                    href = unquote(match.group(1))

            # 检查是否包含目标URL或相关域名
            if any(url in href for url in target_urls) or any(domain in href for domain in ['freellm.top', 'freellm.net', 'github.com']):
                snippets.append({
                    'title': text,
                    'url': href,
                    'extraction_time': datetime.now().isoformat()
                })

        return snippets

    def check_reference_count(self, engine, query, target_url):
        """
        检查某个关键词在某个引擎上的引用次数
        :param engine: 引擎名称
        :param query: 关键词
        :param target_url: 目标URL
        :return: 引用结果
        """
        html = self.search_on_ai_engine(engine, query)
        if not html:
            return None

        snippets = self.extract_snippets(html, target_url)
        return {
            'engine': engine,
            'query': query,
            'reference_count': len(snippets),
            'references': snippets,
            'first_seen': datetime.now().isoformat()
        }

    def analyze_all_keywords(self, keywords):
        """
        分析所有关键词在所有AI引擎上的引用情况
        :param keywords: 关键词列表
        :return: 分析结果汇总
        """
        results = {
            'summary': {},
            'details': {}
        }

        for keyword in keywords:
            print(f"\n🔍 搜索关键词: {keyword}")

            engine_results = {
                'chatgpt': None,
                'perplexity': None,
                'gemini': None
            }

            for engine in ['chatgpt', 'perplexity', 'gemini']:
                print(f"  检查 {engine.upper()}...", end=" ")
                result = self.check_reference_count(engine, keyword, self.target_urls)
                if result:
                    engine_results[engine] = result
                    print(f"✓ 找到 {result['reference_count']} 条引用")
                else:
                    print("✗ 未找到引用")
                time.sleep(1)  # 避免请求过快

            results['details'][keyword] = engine_results
            results['summary'][keyword] = {
                'total_references': sum(
                    r['reference_count'] if r else 0
                    for r in engine_results.values()
                ),
                'engages_with_you': any(r is not None and r['reference_count'] > 0 for r in engine_results.values()),
                'engines_mentioned': [e for e, r in engine_results.items() if r and r['reference_count'] > 0]
            }

        return results

    def save_results(self, results, filename=None):
        """
        保存结果到JSON文件
        :param results: 分析结果
        :param filename: 输出文件名（默认: ai-reference-check-{timestamp}.json）
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            filename = f'ai-reference-check-{timestamp}.json'

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n✓ 结果已保存到: {filename}")
        return filename


def main():
    """主函数"""
    # 目标官网URL
    target_urls = [
        'https://freellm.top/',
        'https://freellm.net/',
        'https://github.com/xdguo-design/freellm'
    ]

    # 关键词列表
    keywords = [
        "free llm api",
        "free gpt-4",
        "open source ai models",
        "no credit card ai",
        "free ai tools",
        "Agnes AI agnes-2.0-flash",
        "Agnes AI agnes-video-v2.0"
    ]

    print("=" * 60)
    print("AI Reference Checker - AI引用检测工具")
    print("=" * 60)
    print(f"\n目标官网: {', '.join(target_urls)}")
    print(f"关键词数量: {len(keywords)}\n")

    # 创建检测器实例
    checker = AIReferenceChecker(target_urls)

    # 执行分析
    start_time = time.time()
    results = checker.analyze_all_keywords(keywords)
    elapsed_time = time.time() - start_time

    # 打印汇总
    print("\n" + "=" * 60)
    print("分析汇总")
    print("=" * 60)
    for keyword, summary in results['summary'].items():
        print(f"\n关键词: {keyword}")
        print(f"  总引用数: {summary['total_references']}")
        print(f"  是否被AI引用: {'✓ 是' if summary['engages_with_you'] else '✗ 否'}")
        print(f"  涉及引擎: {', '.join(summary['engines_mentioned'])}")

    # 保存结果
    print(f"\n总耗时: {elapsed_time:.2f} 秒")
    output_file = checker.save_results(results)
    print(f"📊 完整结果: {output_file}")


if __name__ == '__main__':
    main()
