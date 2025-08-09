# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个HTML转PDF的工具项目，主要功能是将SSH教程的多个HTML文件按目录顺序合并成一个PDF文档，并自动添加书签。

## 常用命令

### 安装依赖
```bash
npm install
```

### 运行HTML转PDF（完整转换）
```bash
node merge_by_toc.js
```

### 测试模式（只转换第一个文件）
```bash
node merge_by_toc.js --test
```

### 添加书签到PDF
```bash
python add_bookmarks.py <pdf文件路径> [书签文件路径] [输出文件路径]
```

### 运行Playwright测试
```bash
npx playwright test
```

## 项目架构

### 核心文件
- `merge_by_toc.js` - 主要的HTML转PDF脚本，使用Playwright和pdf-lib
- `add_bookmarks.py` - Python脚本，用于向PDF添加书签（使用PyPDF2）
- `playwright.config.ts` - Playwright测试配置

### 目录结构
- `src/` - 源HTML文件目录
  - `index.html` - 主页面，包含目录结构
  - `basic.html`, `client.html` 等各章节HTML文件
  - `assets/` - 静态资源（CSS、JS、图片、字体）
- `output/` - 输出目录
  - `document_by_toc.pdf` - 生成的PDF文档
  - `document_by_toc_with_bookmarks.pdf` - 带书签的PDF文档
  - `bookmarks.txt` - 书签信息文件

### 工作流程
1. 解析 `src/index.html` 中的目录结构，获取HTML文件顺序
2. 使用Playwright将每个HTML文件转换为PDF
3. 使用pdf-lib合并所有PDF并添加封面页和目录页
4. 使用Python脚本和PyPDF2添加交互式书签

## 关键依赖

### JavaScript依赖
- **@playwright/test** - 浏览器自动化，用于HTML转PDF
- **pdf-lib** - PDF操作库，用于合并PDF和创建页面
- **@pdf-lib/fontkit** - 字体支持，用于中文字体嵌入
- **cheerio** - HTML解析，用于提取目录结构

### Python依赖（需单独安装）
- **PyPDF2** - PDF书签操作

## 重要说明

### 中文字体支持
- 脚本会自动尝试加载Windows系统字体（黑体、宋体、微软雅黑等）
- 如果无法加载中文字体，将使用英文标题

### 测试模式
- 使用 `--test` 参数可以只转换第一个文件进行测试
- 测试模式的输出文件会添加 `test_` 前缀，避免与正式文件冲突

### 内存管理
- 脚本会定期释放Playwright context内存（每处理3个文件）
- 临时文件会在处理完成后自动清理

### 书签格式
- 书签文件格式：`序号. 章节标题 (第X页)`
- 支持封面页（第1页）和目录页（第2页）的自动书签

## 开发注意事项

### HTML文件要求
- 所有HTML文件必须在 `src/` 目录下
- `index.html` 必须包含正确的目录链接结构
- 链接应使用相对路径（如 `./basic.html`）

### PDF输出
- 默认输出格式：A4纸张，15mm上下边距，10mm左右边距
- 自动添加页眉（章节标题）和页脚（页码）
- 支持背景图片和样式的保留

### 错误处理
- 脚本会跳过不存在的HTML文件并记录警告
- 提供详细的进度信息和错误日志
- 支持部分文件转换失败的情况