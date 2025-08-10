# HTML转PDF转换器

一个强大的工具，功能是将静态网站的html网页转化为带有书签的PDF文件。程序会读取src文件夹里面的index.html（必须用这个名字）,并读取index页面里面的目录层级信息，生成目录书签bookmarks.txt，并且和src文件夹里面的html文件对照检查——目录的结构应该和src文件夹里面的文件夹和文件层级结构对应。然后程序会按照目录的顺序，利用nodejs的playwright库将HTML文件转化合并为1个PDF文件，同时利用python的PyPDF2库将bookmarks.txt转化为pdf的书签。

如果目录层级不只有一级，那么要求src里面的文件夹和文件夹下的html文件与之对应，最终本程序会自动为目录生成PDF的嵌套书签。

这个项目最初是为了将网道(WangDoc.com)的《SSH教程》转换为可下载的PDF格式而开发的。因此，此项目中包含有《SSH教程》的样例文件。

样例文件的原网址：https://wangdoc.com/ssh/

样例文件的Github：https://github.com/wangdoc/ssh-tutorial


## 功能特性

- 📄 将多个HTML文件合并为单个PDF文档
- 📖 根据index.html自动生成目录页
- 🔖 交互式PDF书签，支持层级结构
- 🎨 可自定义的封面页，支持图片
- 🌐 多语言支持（中文/英文）
- 🧪 测试模式，便于快速验证
- 📱 保留响应式设计

## 系统要求

- Node.js (v14或更高版本)
- Python 3.11.x以上 (用于书签功能)
- npm或yarn

## 安装说明

1. 克隆此仓库
```bash
git clone <repository-url>
cd html2pdf
```

2. 安装Node.js依赖
```bash
# 安装本地依赖库
npm install 
# 安装几个无头浏览器
npx install playwright
```

3. 安装Python依赖（用于书签生成）
```bash
# 安装PyPDF2库
pip install PyPDF2
```

## 使用方法
- 将你要转化的静态网页文件的html文件都放置于/src文件夹内，其中必须要包括一个含有目录的Index.html文件作为主页入口。
- index.html的目录结构，和你放在/src文件夹内的html文件结构必须一致。
- css样式文件统一放在/src/assets文件夹内，文件夹结构参考样例。
- 封面可以自定义设计，封面图片必须位于/src文件夹内，命名为fengmian.png。

### 完整转换
根据/src/index.html文件内的目录转换所有HTML文件：
```bash
node merge_by_toc.js
```

### 测试模式
仅转换目录里面的第一个html文件（如果有次级章节会一起转换）用于测试，避免全部转化时间太久：
```bash
node merge_by_toc.js --test
```

### 为PDF添加书签
为现有PDF添加交互式书签：
```bash
# 书签文件默认为bookmarks.txt，输出文件默认为“原文件名_with_bookmarks.pdf”
python add_bookmarks.py <pdf文件> [书签文件] [输出文件]
```

### 使用示例
```bash
# 完整转换，根据Index.html文件内容，自动生成bookmarks.txt，并自动为PDF文件添加书签。
node merge_by_toc.js

# 测试模式
node merge_by_toc.js --test

# 手动为现有PDF添加书签，正常情况下没有必要。
python add_bookmarks.py output/document_by_toc.pdf
python add_bookmarks.py output/document_by_toc.pdf output/bookmarks.txt 
```

## 项目结构

```
html2pdf/
├── src/                    # 源HTML文件
│   ├── index.html         # 包含目录的主页面
│   ├── basic.html         # 各章节文件
│   ├── client.html        # 各章节文件
│   ├── ......             # 其余各章节文件
│   ├── assets/           # 静态资源
│   │   ├── css/          # 样式文件
│   │   ├── js/           # JavaScript文件
│   │   ├── icons/        # 网站图标和应用图标
│   │   └── fonts/        # 字体文件
├── output/               # 生成的文件
│   ├── document_by_toc.pdf              # 主要PDF输出
│   ├── document_by_toc_with_bookmarks.pdf  # 带书签的PDF
│   └── bookmarks.txt     # 书签信息
├── merge_by_toc.js       # 主要转换脚本
├── add_bookmarks.py      # 书签生成脚本
├── toc_parser.py         # bookmarks.txt生成脚本
└── playwright.config.ts  # Playwright配置
```

## 工作原理

1. **解析目录结构**：脚本读取`src/index.html`并提取目录结构
2. **HTML转PDF**：使用Playwright将每个HTML文件转换为PDF
3. **PDF合并**：使用pdf-lib合并所有PDF，添加封面页和目录页
4. **书签生成**：使用PyPDF2为最终PDF添加交互式书签

## 配置说明

### 封面页自定义
- 替换`src/fengmian.png`为您自己的封面图片
- 脚本自动检测图片格式（PNG/JPG）
- 支持封面文字的中文字体

### 样式设置
- 转换过程中自动注入打印专用CSS
- PDF输出中隐藏导航元素
- 代码块和图片针对打印进行了优化

## 输出文件

- `document_by_toc.pdf` - 主要PDF文档
- `document_by_toc_with_bookmarks.pdf` - 带交互式书签的PDF
- `bookmarks.txt` - 包含书签信息的文本文件
- `test_*.*` - 测试模式文件（使用--test参数时）

## 依赖库

### JavaScript
- **@playwright/test** - 浏览器自动化，用于HTML转PDF
- **pdf-lib** - PDF操作和合并
- **@pdf-lib/fontkit** - 字体嵌入支持
- **cheerio** - HTML解析，用于目录提取

### Python
- **PyPDF2** - PDF书签生成

## 浏览器支持

该工具使用Playwright，支持所有现代浏览器：
- 基于Chromium的浏览器
- Firefox
- WebKit (Safari)

## 故障排除

### 字体问题
- 脚本自动尝试从系统加载中文字体
- 如果字体不可用，会回退到英文文本
- 支持的字体：黑体、宋体、微软雅黑、楷体

### 内存管理
- 脚本每处理5个文件自动释放内存
- 转换完成后自动清理临时文件

### 常见问题
- 确保所有HTML文件都存在于`src/`目录中
- 检查`index.html`是否包含正确的目录链接
- 验证Python和PyPDF2是否已安装以支持书签功能

## 许可证

本项目用于教育和个人用途。请尊重原始内容的许可证。

## 贡献指南

1. Fork仓库
2. 创建功能分支
3. 进行更改
4. 充分测试
5. 提交拉取请求

## 原始内容

原始内容遵循知识共享署名-相同方式共享3.0协议。