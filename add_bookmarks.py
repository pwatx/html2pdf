#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF书签添加工具
使用PyPDF2从bookmarks.txt文件读取书签信息并添加到PDF中
"""

import os
import sys
import re
from PyPDF2 import PdfReader, PdfWriter

# 设置输出编码以支持中文显示
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def parse_bookmarks(bookmarks_file):
    """解析书签文件，提取文档标题和章节书签"""
    bookmarks = []
    doc_title = "文档"  # 默认标题
    
    if not os.path.exists(bookmarks_file):
        print(f"[错误] 书签文件不存在: {bookmarks_file}")
        return bookmarks, doc_title
    
    try:
        with open(bookmarks_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取文档标题（格式："文档标题目录："）
        title_match = re.search(r'^(.+?)目录：', content, re.MULTILINE)
        if title_match:
            doc_title = title_match.group(1).strip()
        
        # 使用正则表达式匹配书签条目
        # 格式: "1. 章节标题 (第X页)"
        pattern = r'(\d+)\.\s+(.+?)\s+\(第(\d+)页\)'
        matches = re.findall(pattern, content)
        
        for match in matches:
            index, title, page_num = match
            bookmarks.append({
                'index': int(index),
                'title': title.strip(),
                'page': int(page_num)
            })
        
        print(f"[成功] 从 {bookmarks_file} 中解析到文档标题: {doc_title}")
        print(f"[成功] 解析到 {len(bookmarks)} 个章节书签")
        
    except Exception as e:
        print(f"[错误] 解析书签文件失败: {e}")
    
    return bookmarks, doc_title

def add_bookmarks_to_pdf(pdf_file, bookmarks, doc_title, output_file=None):
    """将书签添加到PDF文件"""
    if not os.path.exists(pdf_file):
        print(f"[错误] PDF文件不存在: {pdf_file}")
        return False
    
    if not bookmarks:
        print("[错误] 没有书签信息")
        return False
    
    try:
        # 读取PDF文件
        print(f"[信息] 正在读取PDF文件: {pdf_file}")
        reader = PdfReader(pdf_file)
        writer = PdfWriter()
        
        # 复制所有页面
        for page in reader.pages:
            writer.add_page(page)
        
        # 添加封面和目录书签
        print("[信息] 正在添加书签...")
        
        # 添加封面书签 (第1页)
        writer.add_outline_item(
            title="封面",
            page_number=0
        )
        print("  [成功] 封面 -> 第1页")
        
        # 添加目录书签 (第2页)
        writer.add_outline_item(
            title="目录",
            page_number=1
        )
        print("  [成功] 目录 -> 第2页")
        
        # 添加章节书签
        for bookmark in bookmarks:
            # PyPDF2中页码从0开始，所以需要减1
            page_index = bookmark['page'] 
            if 0 <= page_index < len(reader.pages):
                writer.add_outline_item(
                    title=bookmark['title'],
                    page_number=page_index
                )
                print(f"  [成功] {bookmark['index']}. {bookmark['title']} -> 第{bookmark['page']}页")
            else:
                print(f"  [警告] 页码超出范围: {bookmark['title']} -> 第{bookmark['page']}页")
        
        # 设置默认页面缩放为125%
        try:
            from PyPDF2.generic import createStringObject, createNumberObject, DictionaryObject
            # 创建ViewerPreferences字典
            viewer_prefs = DictionaryObject()
            viewer_prefs[createStringObject('/FitWindow')] = createStringObject('true')
            viewer_prefs[createStringObject('/DisplayDocTitle')] = createStringObject('true')
            
            # 设置到根对象
            writer._root_object.update({
                createStringObject('/ViewerPreferences'): viewer_prefs
            })
            print("  [成功] 已设置默认视图属性")
        except Exception as e:
            print(f"  [信息] 无法设置默认缩放: {e}")
        
        # 设置输出文件名
        if output_file is None:
            base_name = os.path.splitext(os.path.basename(pdf_file))[0]
            output_file = os.path.join(os.path.dirname(pdf_file), f"{base_name}_with_bookmarks.pdf")
        
        # 保存带书签的PDF
        print(f"[信息] 正在保存带书签的PDF: {output_file}")
        with open(output_file, 'wb') as output:
            writer.write(output)
        
        print(f"[成功] 书签添加成功！输出文件: {output_file}")
        return True
        
    except Exception as e:
        print(f"[错误] 添加书签失败: {e}")
        return False

def main():
    """主函数"""
    print("PDF书签添加工具")
    print("=" * 50)
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python add_bookmarks.py <pdf_file> [bookmarks_file] [output_file]")
        print("")
        print("参数说明:")
        print("  pdf_file: PDF文件路径")
        print("  bookmarks_file: 书签文件路径 (可选，默认为bookmarks.txt)")
        print("  output_file: 输出文件路径 (可选，默认为原文件名_with_bookmarks.pdf)")
        print("")
        print("示例:")
        print("  python add_bookmarks.py output/document_by_toc.pdf")
        print("  python add_bookmarks.py output/document_by_toc.pdf output/bookmarks.txt")
        print("  python add_bookmarks.py output/document_by_toc.pdf output/bookmarks.txt output/document_with_bookmarks.pdf")
        return
    
    # 获取参数
    pdf_file = sys.argv[1]
    bookmarks_file = sys.argv[2] if len(sys.argv) > 2 else "output/bookmarks.txt"
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # 转换为绝对路径
    pdf_file = os.path.abspath(pdf_file)
    bookmarks_file = os.path.abspath(bookmarks_file)
    if output_file:
        output_file = os.path.abspath(output_file)
    
    # 检查PyPDF2是否安装
    try:
        import PyPDF2
    except ImportError:
        print("[错误] 未安装PyPDF2模块")
        print("请运行: pip install PyPDF2")
        return
    
    # 解析书签文件
    bookmarks, doc_title = parse_bookmarks(bookmarks_file)
    
    if not bookmarks:
        print("[错误] 没有找到有效的书签信息")
        return
    
    # 添加书签到PDF
    success = add_bookmarks_to_pdf(pdf_file, bookmarks, doc_title, output_file)
    
    if success:
        print("\n[成功] 书签添加完成！")
        print("现在你可以在PDF阅读器中看到书签面板了。")
    else:
        print("\n[错误] 书签添加失败！")

if __name__ == "__main__":
    main()
