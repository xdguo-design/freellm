#!/usr/bin/env python3
"""
Hreflang Generator - 基于URL列表生成完整的hreflang标签代码
支持多语言站点SEO优化
"""

import json
from datetime import datetime


class HreflangGenerator:
    """Hreflang标签生成器"""

    def __init__(self, url_list, default_language='zh-CN'):
        """
        初始化
        :param url_list: URL列表，格式: [{'url': '...', 'lang': 'zh-CN'}, ...]
        :param default_language: 默认语言
        """
        self.url_list = url_list
        self.default_language = default_language

    def generate_hreflang_tags(self):
        """
        生成完整的hreflang标签代码
        :return: HTML字符串
        """
        tags = []

        # 生成x-default标签
        default_url = self.url_list[0]['url']
        tags.append(f'  <link rel="alternate" hreflang="x-default" href="{default_url}" />')

        # 生成每个语言的hreflang标签
        for item in self.url_list:
            url = item['url']
            lang = item['lang']
            tags.append(f'  <link rel="alternate" hreflang="{lang}" href="{url}" />')

        return '\n'.join(tags)

    def generate_xhtml_hreflang(self):
        """
        生成XHTML格式的hreflang标签
        :return: XHTML代码字符串
        """
        tags = []

        # 生成x-default标签
        default_url = self.url_list[0]['url']
        tags.append(f'  <link rel="alternate" hreflang="x-default" href="{default_url}" />')

        # 生成每个语言的hreflang标签
        for item in self.url_list:
            url = item['url']
            lang = item['lang']
            tags.append(f'  <link rel="alternate" hreflang="{lang}" href="{url}" />')

        xhtml_code = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <!-- x-default -->
  <xhtml:link rel="alternate" hreflang="x-default" href="{default_url}" />
{chr(10).join(tags)}
</urlset>'''

        return xhtml_code

    def generate_seo_meta(self):
        """
        生成SEO友好的meta标签
        :return: HTML字符串
        """
        meta_tags = []

        for item in self.url_list:
            url = item['url']
            lang = item['lang']
            # 生成alternates标签（替代hreflang）
            meta_tags.append(f'  <link rel="alternate" hreflang="{lang}" href="{url}" />')

        return '\n'.join(meta_tags)

    def generate_sitemap_entry(self):
        """
        生成sitemap.xml条目格式
        :return: XML字符串
        """
        entries = []

        for item in self.url_list:
            url = item['url']
            lang = item['lang']
            lastmod = datetime.now().strftime('%Y-%m-%d')
            priority = '0.8' if lang == self.default_language else '0.6'
            freq = 'daily' if lang == self.default_language else 'weekly'

            entries.append(f'''  <url>
    <loc>{url}</loc>
    <lastmod>{lastmod}</lastmod>
    <priority>{priority}</priority>
    <changefreq>{freq}</changefreq>
    <xhtml:link rel="alternate" hreflang="x-default" href="{self.url_list[0]['url']}" />
    <xhtml:link rel="alternate" hreflang="{lang}" href="{url}" />
  </url>''')

        return '\n'.join(entries)

    def generate_report(self):
        """
        生成分析报告
        :return: 报文字典
        """
        languages = [item['lang'] for item in self.url_list]
        default_count = sum(1 for item in self.url_list if item['lang'] == self.default_language)
        other_count = len(self.url_list) - default_count

        return {
            'total_languages': len(languages),
            'languages': sorted(set(languages)),
            'default_language': self.default_language,
            'default_count': default_count,
            'other_count': other_count,
            'generated_at': datetime.now().isoformat()
        }


def main():
    """主函数"""

    # 示例URL列表
    url_list = [
        {'url': 'https://freellm.top/', 'lang': 'zh-CN'},
        {'url': 'https://freellm.top/?lang=en', 'lang': 'en'},
        {'url': 'https://freellm.net/', 'lang': 'zh-CN'},
        {'url': 'https://freellm.net/?lang=en', 'lang': 'en'},
        {'url': 'https://github.com/xdguo-design/freellm', 'lang': 'en'}
    ]

    print("=" * 70)
    print("Hreflang Generator - 多语言SEO标签生成器")
    print("=" * 70)
    print(f"\n检测到 {len(url_list)} 个语言版本\n")

    # 创建生成器实例
    generator = HreflangGenerator(url_list, default_language='zh-CN')

    # 生成报告
    report = generator.generate_report()
    print("📊 分析报告:")
    print(f"  - 总语言数: {report['total_languages']}")
    print(f"  - 支持语言: {', '.join(report['languages'])}")
    print(f"  - 默认语言: {report['default_language']} ({report['default_count']} 个)")
    print(f"  - 其他语言: {report['other_count']} 个")
    print(f"  - 生成时间: {report['generated_at']}")

    # 生成HTML格式
    print("\n" + "-" * 70)
    print("HTML格式:")
    print("-" * 70)
    html_tags = generator.generate_hreflang_tags()
    print(f'''<!-- hreflang标签 - HTML -->
<head>
{html_tags}
</head>''')

    # 生成XHTML格式
    print("\n" + "-" * 70)
    print("XHTML格式:")
    print("-" * 70)
    xhtml_code = generator.generate_xhtml_hreflang()
    print(xhtml_code)

    # 生成Sitemap条目
    print("\n" + "-" * 70)
    print("Sitemap.xml条目:")
    print("-" * 70)
    sitemap_entry = generator.generate_sitemap_entry()
    print(sitemap_entry)

    # 保存到文件
    output_file = f'hreflang-{datetime.now().strftime("%Y%m%d-%H%M%S")}.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f'''<!-- Hreflang Generator - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} -->
<!-- 自动生成日期: {report['generated_at']} -->
<!-- 总语言数: {report['total_languages']} -->

<!-- 在<head>中添加以下标签 -->
<head>
{html_tags}
</head>

<!-- 可选: XHTML格式 -->
<xhtml:link rel="alternate" hreflang="x-default" href="{url_list[0]['url']}" />
{chr(10).join([f'<xhtml:link rel="alternate" hreflang="{item["lang"]}" href="{item["url"]}" />' for item in url_list])}
''')
    print(f"\n✓ 完整代码已保存到: {output_file}")

    # 生成JSON配置
    json_file = f'hreflang-config-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(url_list, f, ensure_ascii=False, indent=2)
    print(f"✓ URL配置已保存到: {json_file}")


if __name__ == '__main__':
    main()
