#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目录解析模块
从index.html中解析多级目录结构，支持嵌套的章节和子章节
"""

import os
import re
import sys
from typing import List, Dict, Any
from pathlib import Path
from bs4 import BeautifulSoup


class TOCParser:
    def __init__(self):
        pass
    
    def parse_toc(self, html_content: str) -> Dict[str, Any]:
        """
        解析HTML内容，提取多级目录结构
        """
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 找到菜单容器
        menu_container = soup.find('aside', class_='menu')
        if not menu_container:
            raise ValueError('无法找到菜单容器')
        
        # 找到主要的ul列表
        main_ul = menu_container.find('ul', class_='menu-list')
        if not main_ul:
            main_ul = menu_container.find('ul')
        
        if not main_ul:
            raise ValueError('无法找到目录列表')
        
        # 解析层级结构
        hierarchical_toc = self._parse_hierarchical_structure(main_ul)
        
        # 扁平化结构
        flat_toc = self._flatten_hierarchy(hierarchical_toc)
        
        return {
            'hierarchical': hierarchical_toc,
            'flat': flat_toc,
            'total_items': len(flat_toc)
        }
    
    def _parse_hierarchical_structure(self, main_ul) -> List[Dict[str, Any]]:
        """
        解析层级结构
        """
        items = []
        
        # 解析主列表中的li项
        for li in main_ul.find_all('li', recursive=False):
            # 查找a标签
            a_tag = li.find('a', href=True)
            if a_tag and a_tag['href'].endswith('.html'):
                href = a_tag['href']
                
                # 查找标题文本
                title_span = a_tag.find('span', class_='menu-list-title')
                if title_span:
                    title = title_span.get_text().strip()
                    
                    # 检查是否包含子ul
                    children = []
                    sub_ul = li.find('ul')
                    if sub_ul:
                        children = self._parse_hierarchical_structure(sub_ul)
                    
                    item = {
                        'href': href,
                        'title': title,
                        'level': 1,
                        'children': children,
                        'is_folder': len(children) > 0
                    }
                    items.append(item)
        
        return items
    
    def _flatten_hierarchy(self, hierarchical: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        将层级结构扁平化，生成连续的索引
        """
        flat = []
        index_counter = 1
        
        def flatten_items(items, level=1):
            nonlocal index_counter
            
            for item in items:
                # 为当前项生成索引
                display_index = str(index_counter)
                flat_item = {
                    'href': item['href'],
                    'title': item['title'],
                    'level': item['level'],
                    'index': len(flat) + 1,
                    'display_index': display_index,
                    'has_children': len(item['children']) > 0
                }
                flat.append(flat_item)
                
                # 处理子项目
                if item['children']:
                    # 为每个子项目生成带前缀的索引
                    for i, child in enumerate(item['children']):
                        child_display_index = f"{display_index}.{i + 1}"
                        flat_child = {
                            'href': child['href'],
                            'title': child['title'],
                            'level': child['level'],
                            'index': len(flat) + 1,
                            'display_index': child_display_index,
                            'has_children': False
                        }
                        flat.append(flat_child)
                
                index_counter += 1
        
        flatten_items(hierarchical)
        return flat
    
    def validate_toc_files(self, flat_toc: List[Dict[str, Any]], src_dir: str) -> Dict[str, Any]:
        """
        验证目录文件是否存在
        """
        valid_files = []
        missing_files = []
        
        src_path = Path(src_dir)
        
        for item in flat_toc:
            file_path = src_path / item['href']
            if file_path.exists():
                valid_files.append(item)
            else:
                missing_files.append({
                    **item,
                    'file_path': str(file_path)
                })
        
        return {
            'valid_files': valid_files,
            'missing_files': missing_files,
            'total_valid': len(valid_files),
            'total_missing': len(missing_files)
        }
    
    def generate_bookmark_text(self, flat_toc: List[Dict[str, Any]], doc_title: str, total_pages: int = 0) -> str:
        """
        生成书签文本（按照模板格式）
        """
        bookmark_lines = []
        
        for item in flat_toc:
            # 根据层级添加缩进（模板使用4个空格的缩进）
            if item['level'] == 1:
                indent = ''
            else:
                indent = '    ' * (item['level'] - 1)
            
            # 构建书签条目，格式：序号.标题(第X页)
            # 注意：这里页码是预估的，实际页码需要在PDF生成后确定
            estimated_page = 3 + item['index'] - 1  # 从第3页开始（封面+目录）
            bookmark_line = f"{indent}{item['display_index']}.{item['title']}(第{estimated_page}页)"
            bookmark_lines.append(bookmark_line)
        
        return f"{doc_title}目录：\n\n{chr(10).join(bookmark_lines)}\n\n总页数：{total_pages}"
    
    def generate_pdf_bookmarks(self, flat_toc: List[Dict[str, Any]], start_page: int = 3) -> List[Dict[str, Any]]:
        """
        生成PDF书签数据
        """
        bookmarks = []
        
        for item in flat_toc:
            bookmark = {
                'title': item['title'],
                'level': item['level'],
                'page_index': start_page + item['index'] - 1,
                'display_index': item['display_index']
            }
            bookmarks.append(bookmark)
        
        return bookmarks
    
    def generate_bookmarks_file(self, flat_toc: List[Dict[str, Any]], doc_title: str, output_file: str = 'output/bookmarks.txt', page_map: Dict[str, int] = None) -> str:
        """
        生成符合模板格式的bookmarks.txt文件
        """
        bookmark_lines = []
        
        for item in flat_toc:
            # 根据display_index的层级添加缩进（模板使用4个空格的缩进）
            if '.' in item['display_index']:
                # 子章节，根据点的数量确定缩进
                level = item['display_index'].count('.')
                indent = '    ' * level
            else:
                # 主章节，无缩进
                indent = ''
            
            # 使用实际页码或预估页码
            actual_page = None
            if page_map and item['title'] in page_map:
                # PDF页码从0开始，但书签显示从1开始
                actual_page = page_map[item['title']] + 1
            else:
                # 构建书签条目，严格按照模板格式
                # 主章节：序号.标题(第X页)  子章节：序号 标题(第X页)
                # 注意：这里页码是预估的，实际页码需要在PDF生成后确定
                actual_page = 2 + item['index']  # 从第3页开始（封面+目录）
            
            # 判断是否为主章节（不包含点的序号）
            if '.' not in item['display_index']:
                # 主章节，序号和标题之间用点
                bookmark_line = f"{indent}{item['display_index']}.{item['title']}(第{actual_page}页)"
            else:
                # 子章节，序号和标题之间用空格
                bookmark_line = f"{indent}{item['display_index']} {item['title']}(第{actual_page}页)"
            bookmark_lines.append(bookmark_line)
        
        # 生成完整的书签文本，严格按照模板格式：只有书签条目，没有标题和总页数
        bookmark_text = chr(10).join(bookmark_lines)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir:  # 只有当目录不为空时才创建
            os.makedirs(output_dir, exist_ok=True)
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(bookmark_text)
        
        return output_file
    
    def extract_document_title(self, html_file_path: str) -> str:
        """
        从HTML文件中提取文档标题
        """
        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 尝试从<title>标签提取
            title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
                # 清理标题中的多余内容
                title = re.sub(r'\s*-\s*.*$', '', title)  # 移除" - 作者名"等后缀
                title = re.sub(r'\s*\|\s*.*$', '', title)  # 移除" | 网站名"等后缀
                if title:
                    return title
            
            # 尝试从<h1>标签提取
            h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE)
            if h1_match:
                return h1_match.group(1).strip()
            
            # 尝试从<meta>标签提取
            meta_title_match = re.search(r'<meta[^>]*name=["\']title["\'][^>]*content=["\']([^"\']*)["\']',
                                          content, re.IGNORECASE)
            if meta_title_match:
                return meta_title_match.group(1).strip()
            
            # 返回默认标题
            return "文档"
            
        except Exception as e:
            print(f"[WARNING] 提取文档标题失败: {e}")
            return "文档"
    
    def parse_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        从文件解析目录
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return self.parse_toc(html_content)
    
    def scan_directory_structure(self, src_dir: str) -> Dict[str, Any]:
        """
        扫描src文件夹的实际文件结构
        返回目录结构和文件列表
        """
        src_path = Path(src_dir)
        if not src_path.exists():
            raise FileNotFoundError(f"src目录不存在: {src_dir}")
        
        structure = []
        files = []
        
        # 扫描根目录的HTML文件
        root_html_files = [f for f in src_path.glob('*.html') if f.name != 'index.html']
        
        for html_file in root_html_files:
            relative_path = html_file.relative_to(src_path)
            files.append({
                'path': str(relative_path),
                'name': html_file.name,
                'size': html_file.stat().st_size,
                'type': 'file',
                'level': 0
            })
        
        # 扫描子目录，但忽略assets文件夹
        subdirs = [d for d in src_path.iterdir() if d.is_dir() and not d.name.startswith('.') and d.name != 'assets']
        
        for subdir in sorted(subdirs):
            dir_info = {
                'name': subdir.name,
                'path': str(subdir.relative_to(src_path)),
                'type': 'directory',
                'level': 0,
                'files': [],
                'subdirs': []
            }
            
            # 扫描子目录中的文件
            dir_files = [f for f in subdir.glob('*.html') if f.name != 'index.html']
            for file in sorted(dir_files):
                relative_path = file.relative_to(src_path)
                file_info = {
                    'path': str(relative_path),
                    'name': file.name,
                    'size': file.stat().st_size,
                    'type': 'file',
                    'level': 1
                }
                files.append(file_info)
                dir_info['files'].append(file_info)
            
            # 扫描子目录的子目录
            sub_subdirs = [d for d in subdir.iterdir() if d.is_dir() and not d.name.startswith('.')]
            for sub_subdir in sorted(sub_subdirs):
                sub_subdir_info = {
                    'name': sub_subdir.name,
                    'path': str(sub_subdir.relative_to(src_path)),
                    'type': 'directory',
                    'level': 1,
                    'files': []
                }
                
                # 扫描子子目录中的文件
                sub_subdir_files = [f for f in sub_subdir.glob('*.html') if f.name != 'index.html']
                for file in sorted(sub_subdir_files):
                    relative_path = file.relative_to(src_path)
                    file_info = {
                        'path': str(relative_path),
                        'name': file.name,
                        'size': file.stat().st_size,
                        'type': 'file',
                        'level': 2
                    }
                    files.append(file_info)
                    sub_subdir_info['files'].append(file_info)
                
                dir_info['subdirs'].append(sub_subdir_info)
            
            structure.append(dir_info)
        
        return {
            'structure': structure,
            'files': files,
            'total_files': len(files),
            'total_dirs': len(structure) + sum(len(d['subdirs']) for d in structure)
        }
    
    def generate_file_structure_text(self, structure_data: Dict[str, Any]) -> str:
        """
        生成文件结构文本
        """
        lines = []
        lines.append("src/ 文件夹结构:")
        lines.append("=" * 50)
        lines.append("")
        
        # 添加根目录文件
        root_files = [f for f in structure_data['files'] if f['level'] == 0]
        if root_files:
            lines.append("根目录文件:")
            for file in sorted(root_files, key=lambda x: x['name']):
                lines.append(f"  📄 {file['name']}")
            lines.append("")
        
        # 添加目录结构
        for dir_info in sorted(structure_data['structure'], key=lambda x: x['name']):
            lines.append(f"📁 {dir_info['name']}/")
            
            # 添加目录中的文件
            for file in sorted(dir_info['files'], key=lambda x: x['name']):
                lines.append(f"    📄 {file['name']}")
            
            # 添加子目录
            for sub_dir in sorted(dir_info['subdirs'], key=lambda x: x['name']):
                lines.append(f"    📁 {sub_dir['name']}/")
                for file in sorted(sub_dir['files'], key=lambda x: x['name']):
                    lines.append(f"        📄 {file['name']}")
            
            lines.append("")
        
        # 添加统计信息
        lines.append("=" * 50)
        lines.append(f"总计: {structure_data['total_files']} 个文件, {structure_data['total_dirs']} 个目录")
        
        return '\n'.join(lines)
    
    def generate_file_structure_file(self, src_dir: str, output_file: str = 'output/file_structure.txt') -> str:
        """
        生成file_structure.txt文件
        """
        # 扫描目录结构
        structure_data = self.scan_directory_structure(src_dir)
        
        # 生成文件结构文本
        structure_text = self.generate_file_structure_text(structure_data)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(structure_text)
        
        return output_file
    
    def validate_directory_structure(self, hierarchical_toc: List[Dict[str, Any]], src_dir: str, level: int = 1) -> Dict[str, Any]:
        """
        验证目录结构与实际文件结构是否匹配
        返回验证结果，包括警告和错误信息
        """
        warnings = []
        errors = []
        
        src_path = Path(src_dir)
        
        for item in hierarchical_toc:
            href = item['href']
            file_path = src_path / href
            
            # 检查主章节对应的目录结构
            if level == 1:
                base_name = Path(href).stem
                expected_dir = src_path / base_name
                
                # 检查是否存在对应的子目录
                if expected_dir.exists():
                    # 检查HTML中的子章节数量与目录中的文件数量是否匹配
                    html_children = item.get('children', [])
                    
                    # 获取目录中的HTML文件
                    if expected_dir.is_dir():
                        dir_html_files = list(expected_dir.glob('*.html'))
                        dir_html_files = [f for f in dir_html_files if f.name != 'index.html']
                        
                        if len(html_children) != len(dir_html_files):
                            warning_msg = f"主章节 '{item['title']}' 的HTML子章节数量({len(html_children)})与目录中文件数量({len(dir_html_files)})不匹配"
                            warnings.append({
                                'type': 'mismatch_count',
                                'chapter': item['title'],
                                'html_count': len(html_children),
                                'dir_count': len(dir_html_files),
                                'message': warning_msg
                            })
                        
                        # 检查是否有HTML中未包含的文件
                        dir_file_names = set(f.name for f in dir_html_files)
                        html_file_names = set(child['href'] for child in html_children)
                        missing_in_html = dir_file_names - html_file_names
                        
                        if missing_in_html:
                            warning_msg = f"目录 '{base_name}/' 中存在HTML未包含的文件: {', '.join(missing_in_html)}"
                            warnings.append({
                                'type': 'missing_in_html',
                                'chapter': item['title'],
                                'missing_files': list(missing_in_html),
                                'message': warning_msg
                            })
                
                # 检查是否有子目录但没有在HTML中定义子章节
                elif len(item.get('children', [])) > 0:
                    # HTML中有子章节，但对应的目录不存在
                    pass  # 这不是错误，因为子章节可能是单独的HTML文件
            
            # 递归检查子章节
            if item.get('children', []):
                child_result = self.validate_directory_structure(item['children'], src_dir, level + 1)
                warnings.extend(child_result['warnings'])
                errors.extend(child_result['errors'])
        
        return {
            'warnings': warnings,
            'errors': errors,
            'total_warnings': len(warnings),
            'total_errors': len(errors)
        }


def main():
    """
    主函数：解析目录结构并生成书签文件
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='目录解析器')
    parser.add_argument('--test', action='store_true', help='测试模式，生成test_bookmarks.txt')
    parser.add_argument('--page-map', type=str, help='页码映射JSON字符串')
    
    args = parser.parse_args()
    
    # 解析页码映射
    page_map = None
    if args.page_map:
        try:
            import json
            page_map = json.loads(args.page_map)
        except Exception as e:
            print(f'[WARNING] 页码映射解析失败: {e}')
    
    toc_parser = TOCParser()
    
    try:
        # 解析当前项目的index.html
        index_html_path = os.path.join(os.getcwd(), 'src', 'index.html')
        
        # 设置UTF-8输出编码以解决Windows命令行乱码问题
        import sys
        if sys.platform == 'win32':
            sys.stdout.reconfigure(encoding='utf-8')
        
        print('[INFO] 正在解析目录结构...')
        result = toc_parser.parse_from_file(index_html_path)
        
        # 验证文件存在性
        print('[INFO] 验证文件存在性...')
        validation = toc_parser.validate_toc_files(result['flat'], os.path.join(os.getcwd(), 'src'))
        
        # 验证目录结构
        print('[INFO] 验证目录结构...')
        structure_validation = toc_parser.validate_directory_structure(result['hierarchical'], os.path.join(os.getcwd(), 'src'))
        
        # 输出解析结果摘要
        print('[INFO] 解析结果:')
        print(f'   总条目数: {result["total_items"]}')
        print(f'   层级深度: {max(item["level"] for item in result["flat"])}')
        print(f'   有效文件: {validation["total_valid"]}')
        print(f'   缺失文件: {validation["total_missing"]}')
        print(f'   结构警告: {structure_validation["total_warnings"]}')
        print(f'   结构错误: {structure_validation["total_errors"]}')
        
        # 显示警告信息
        if structure_validation['warnings']:
            print('\n[WARN] 结构验证警告:')
            for warning in structure_validation['warnings']:
                print(f'   {warning["message"]}')
        
        # 显示错误信息
        if structure_validation['errors']:
            print('\n[ERROR] 结构验证错误:')
            for error in structure_validation['errors']:
                print(f'   {error["message"]}')
        
        # 显示缺失文件
        if validation['missing_files']:
            print('\n[ERROR] 缺失文件:')
            for file in validation['missing_files']:
                print(f'   {file["display_index"]}. {file["title"]} -> {file["file_path"]}')
        
        # 生成文件结构文件
        print('\n[INFO] 生成文件结构文件...')
        try:
            structure_file = toc_parser.generate_file_structure_file(os.path.join(os.getcwd(), 'src'))
            print(f'[INFO] 文件结构文件已生成: {structure_file}')
        except Exception as e:
            print(f'[WARNING] 生成文件结构文件失败: {e}')
        
        # 如果没有错误，生成书签文件
        if structure_validation['total_errors'] == 0 and validation['total_missing'] == 0:
            print('\n[INFO] 生成书签文件...')
            # 从HTML中提取文档标题
            doc_title = toc_parser.extract_document_title(index_html_path)
            
            # 根据模式生成不同的文件名
            if args.test:
                bookmarks_file = 'output/test_bookmarks.txt'
                # 在测试模式下，只使用第一个章节及其子章节
                if result['flat']:
                    # 找到第一个主章节
                    first_chapter = None
                    for item in result['flat']:
                        if '.' not in item['display_index']:
                            first_chapter = item['display_index']
                            break
                    
                    # 如果找到了第一个主章节，只保留该章节及其直接子章节
                    if first_chapter:
                        filtered_toc = [item for item in result['flat'] 
                                      if (item['display_index'] == first_chapter or 
                                          item['display_index'].startswith(first_chapter + '.'))]
                        toc_parser.generate_bookmarks_file(filtered_toc, doc_title, bookmarks_file, page_map)
                    else:
                        # 如果没有找到主章节，只保留前4个项目（第一个章节+3个子章节）
                        toc_parser.generate_bookmarks_file(result['flat'][:4], doc_title, bookmarks_file, page_map)
            else:
                bookmarks_file = 'output/bookmarks.txt'
                toc_parser.generate_bookmarks_file(result['flat'], doc_title, bookmarks_file, page_map)
            
            print(f'[INFO] 书签文件已生成: {bookmarks_file}')
        else:
            print('\n[ERROR] 由于存在错误，跳过书签文件生成')
        
        print('\n[SUCCESS] 目录解析完成')
        
    except Exception as e:
        print(f'[ERROR] 解析失败: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    # 设置输出编码以支持中文显示
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    main()
 