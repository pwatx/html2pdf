const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { PDFDocument, rgb } = require('pdf-lib');
const fontkit = require('@pdf-lib/fontkit');
const cheerio = require('cheerio');

// 添加书签到PDF的函数
async function addBookmarksToPdf(pdfBytes, bookmarks, docInfo) {
  // 由于pdf-lib的限制，我们使用一个简化的方法来添加书签
  // 这里我们创建一个新的PDF文档并添加书签信息
  const pdfDoc = await PDFDocument.load(pdfBytes);
  
  // 添加文档信息（从HTML中提取）
  pdfDoc.setTitle(docInfo.title);
  pdfDoc.setAuthor(docInfo.author);
  pdfDoc.setSubject(docInfo.subject);
  pdfDoc.setKeywords(docInfo.keywords);
  
  // 注意：pdf-lib不直接支持书签，但我们可以设置文档属性
  // 实际的书签功能需要更复杂的PDF操作库
  
  return await pdfDoc.save();
}

// 清理文件名，移除不适合作为文件名的字符
function sanitizeFilename(filename) {
  // 移除或替换不适合文件名的字符
  return filename
    .replace(/[\/\\:*?"<>|]/g, '')  // 移除 / \ : * ? " < > |
    .replace(/^\s+|\s+$/g, '')      // 移除首尾空格
    .replace(/\s+/g, '_')           // 空格替换为下划线
    .replace(/_+/g, '_')            // 多个下划线合并为一个
    .substring(0, 100);              // 限制长度
}

// 从HTML中提取文档信息
function extractDocumentInfo($) {
  const title = $('title').text().trim() || '文档';
  const mainTitle = $('h1.title').text().trim() || title;
  const authorInfo = $('.page-meta p').text().trim() || '';
  const description = $('article.content p').first().text().trim() || '';
  
  // 提取作者名称
  let author = 'Unknown';
  if (authorInfo.includes('（') && authorInfo.includes('）')) {
    author = authorInfo.match(/（(.+?)）/)[1] || authorInfo.split('，')[0];
  } else if (authorInfo.includes('(') && authorInfo.includes(')')) {
    author = authorInfo.match(/\((.+?)\)/)[1] || authorInfo.split(',')[0];
  } else {
    author = authorInfo.split('，')[0] || 'Unknown';
  }
  
  // 提取关键词（从标题和描述中）
  const keywords = [];
  if (mainTitle) keywords.push(mainTitle);
  if (description) {
    // 从描述中提取关键词
    const descWords = description.split(/[，。、\s,\.]+/).filter(word => word.length > 1);
    keywords.push(...descWords.slice(0, 3));
  }
  
  // 提取封面图片文件名
  let coverImage = 'fengmian.png'; // 默认文件名
  const firstImage = $('article.content img').first();
  if (firstImage.length > 0) {
    const src = firstImage.attr('src');
    if (src && !src.startsWith('http')) {
      // 如果是相对路径的本地图片，使用它作为封面
      coverImage = src.split('/').pop(); // 只取文件名部分
    }
  }
  
  return {
    title: mainTitle,
    author: author,
    subject: description,
    keywords: keywords.slice(0, 5),
    coverImage: coverImage
  };
}

(async () => {
  let browser = null;
  let context = null;
  let tempDir = null;
  
  try {
    // 启动浏览器
    browser = await chromium.launch();
    context = await browser.newContext();
    
    // 获取当前目录和文件路径
    const currentDir = process.cwd();
    const srcDir = path.join(currentDir, 'src');
    const outputDir = path.join(currentDir, 'output');
    
    // 确保输出目录存在
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }
    
    // 读取index.html并解析目录顺序
    const indexHtmlPath = path.join(srcDir, 'index.html');
    
    if (!fs.existsSync(indexHtmlPath)) {
      throw new Error('index.html文件不存在，请确保文件在src目录中');
    }
    
    const indexHtmlContent = fs.readFileSync(indexHtmlPath, 'utf8');
    
    // 使用cheerio解析HTML
    const $ = cheerio.load(indexHtmlContent);
    
    // 提取文档信息
    const docInfo = extractDocumentInfo($);
    console.log('📄 文档信息:');
    console.log(`   标题: ${docInfo.title}`);
    console.log(`   作者: ${docInfo.author}`);
    console.log(`   主题: ${docInfo.subject}`);
    console.log(`   关键词: ${docInfo.keywords.join(', ')}`);
    
    // 提取目录链接
    const tocLinks = [];
    
    // 尝试常见目录选择器
    const tocSelectors = [
      '.panel-menu a[href$=".html"]',
      '.menu-list a[href$=".html"]',
      '.toc a[href$=".html"]',
      '.sidebar a[href$=".html"]',
      '#toc a[href$=".html"]',
      'ul.toc a[href$=".html"]',
      'ol.toc a[href$=".html"]',
      'div.toc a[href$=".html"]'
    ];
    
    let tocElement = null;
    for (const selector of tocSelectors) {
      tocElement = $(selector);
      if (tocElement.length > 0) break;
    }
    
    if (!tocElement || tocElement.length === 0) {
      throw new Error('无法在index.html中找到目录结构，请检查HTML结构');
    }
    
    tocElement.each((index, element) => {
      const href = $(element).attr('href');
      const text = $(element).text().trim();
      
      // 只添加有效的HTML文件链接
      if (href && href.endsWith('.html') && !href.startsWith('http')) {
        tocLinks.push({
          href: href.split('#')[0], // 移除锚点
          text
        });
      }
    });
    
    console.log(`从目录中找到 ${tocLinks.length} 个HTML文件`);
    
    if (tocLinks.length === 0) {
      throw new Error('没有找到有效的HTML文件链接');
    }
    
    // 测试模式：只转换第一个章节及其直接子文件
    const testMode = process.argv.includes('--test');
    let filesToProcess = tocLinks;
    
    if (testMode) {
      // 在测试模式下，只转换第一个章节及其直接子文件
      const firstFile = tocLinks[0];
      const firstFileDir = path.dirname(firstFile.href);
      
      // 筛选出第一个章节文件及其直接子文件
      filesToProcess = tocLinks.filter(link => {
        const linkDir = path.dirname(link.href);
        // 包含第一个章节文件本身
        if (link.href === firstFile.href) return true;
        // 只包含直接子文件（在同一目录下且不是目录本身）
        return linkDir === firstFileDir && linkDir !== '.';
      });
      
      console.log(`🧪 测试模式：转换第一个章节及其直接子文件 (${filesToProcess.length} 个文件)`);
    }
    
    // 创建临时目录（根据模式区分，避免冲突）
    tempDir = path.join(outputDir, testMode ? 'temp_pdf_test' : 'temp_pdf');
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir);
    }
    
    // 创建最终PDF文档
    const mergedPdf = await PDFDocument.create();
    mergedPdf.registerFontkit(fontkit);
    
    // 书签相关变量
    const bookmarks = [];
    let currentPageIndex = 0;
    
    // 添加封面页 (使用支持中文的字体)
    const coverPage = mergedPdf.addPage([595, 842]); // A4尺寸
    currentPageIndex++; // 封面页是第1页
    
    // 尝试加载中文字体，如果失败则使用英文
    let font;
    try {
      // 尝试多种中文字体
      const fontPaths = [
        path.join(process.env.SYSTEMROOT || 'C:\\Windows', 'Fonts', 'simhei.ttf'),
        path.join(process.env.SYSTEMROOT || 'C:\\Windows', 'Fonts', 'simsun.ttc'),
        path.join(process.env.SYSTEMROOT || 'C:\\Windows', 'Fonts', 'msyh.ttc'),
        path.join(process.env.SYSTEMROOT || 'C:\\Windows', 'Fonts', 'simkai.ttf')
      ];
      
      for (const fontPath of fontPaths) {
        if (fs.existsSync(fontPath)) {
          try {
            const fontBytes = fs.readFileSync(fontPath);
            font = await mergedPdf.embedFont(fontBytes);
            console.log(`✓ 成功加载字体: ${path.basename(fontPath)}`);
            break;
          } catch (fontError) {
            console.warn(`⚠️ 无法加载字体 ${path.basename(fontPath)}: ${fontError.message}`);
            continue;
          }
        }
      }
      
      if (!font) {
        console.warn('⚠️ 无法加载任何中文字体，将使用英文标题');
      }
    } catch (error) {
      console.warn('⚠️ 字体加载过程中出现错误:', error.message);
    }
    
    // 尝试加载封面图片
    let coverImage = null;
    try {
      const coverImagePath = path.join(srcDir, docInfo.coverImage);
      if (fs.existsSync(coverImagePath)) {
        const imageBytes = fs.readFileSync(coverImagePath);
        // 尝试不同的图片格式
        try {
          coverImage = await mergedPdf.embedPng(imageBytes);
          console.log('✓ 成功加载封面图片 (PNG格式)');
        } catch (pngError) {
          try {
            coverImage = await mergedPdf.embedJpg(imageBytes);
            console.log('✓ 成功加载封面图片 (JPG格式)');
          } catch (jpgError) {
            console.warn('⚠️ 无法识别图片格式，尝试作为PNG处理');
            coverImage = await mergedPdf.embedPng(imageBytes);
            console.log('✓ 成功加载封面图片');
          }
        }
      } else {
        console.warn(`⚠️ 封面图片文件不存在: ${docInfo.coverImage}`);
      }
    } catch (error) {
      console.warn('⚠️ 无法加载封面图片:', error.message);
    }
    
    if (coverImage) {
      // 计算图片尺寸和位置（上半部分）
      const pageWidth = 595;
      const pageHeight = 842;
      const imageWidth = pageWidth - 40; // 左右各留20mm边距
      const imageHeight = pageHeight * 0.6; // 图片占页面高度的60%
      
      // 绘制图片
      coverPage.drawImage(coverImage, {
        x: 20,
        y: pageHeight - imageHeight - 20,
        width: imageWidth,
        height: imageHeight
      });
      
      // 在图片下方绘制文字
      if (font) {
        // 主标题
        coverPage.drawText(docInfo.title, {
          x: 150,
          y: pageHeight - imageHeight - 80,
          size: 48,
          font: font
        });
        // 副标题
        coverPage.drawText(`——by ${docInfo.author}`, {
          x: 150,
          y: pageHeight - imageHeight - 120,
          size: 24,
          font: font
        });
      } else {
        // 主标题
        coverPage.drawText(docInfo.title, {
          x: 150,
          y: pageHeight - imageHeight - 80,
          size: 48
        });
        // 副标题
        coverPage.drawText(`——by ${docInfo.author}`, {
          x: 150,
          y: pageHeight - imageHeight - 120,
          size: 24
        });
      }
    } else {
      // 如果没有图片，使用原来的纯文字设计
      if (font) {
        // 主标题
        coverPage.drawText(docInfo.title, {
          x: 150,
          y: 450,
          size: 48,
          font: font
        });
        // 副标题
        coverPage.drawText(`——by ${docInfo.author}`, {
          x: 150,
          y: 400,
          size: 24,
          font: font
        });
      } else {
        // 主标题
        coverPage.drawText(docInfo.title, {
          x: 150,
          y: 450,
          size: 48
        });
        // 副标题
        coverPage.drawText(`——by ${docInfo.author}`, {
          x: 150,
          y: 400,
          size: 24
        });
      }
    }
    
    // 批量转换并合并（按目录顺序）
    let successCount = 0;
    let failCount = 0;
    
    // 用于记录每个章节的实际起始页码
    const chapterPageMap = new Map();
    
    // 先收集所有章节信息，用于生成带层级的目录页
    const chapterInfo = [];
    
    for (const [index, link] of filesToProcess.entries()) {
      const htmlFile = link.href;
      const htmlPath = path.resolve(srcDir, htmlFile);
      
      // 检查文件是否存在
      if (!fs.existsSync(htmlPath)) {
        console.warn(`⚠️ 文件不存在: ${htmlFile}，跳过`);
        failCount++;
        continue;
      }
      
      // 收集章节信息
      chapterInfo.push({
        index: index + 1,
        text: link.text,
        file: htmlFile
      });
    }
    
    // 添加目录页（在收集完章节信息后生成）
    const tocPages = [];
    let tocPage = mergedPdf.addPage([595, 842]);
    tocPages.push(tocPage);
    currentPageIndex++; // 目录页是第2页
    let yPosition = 700;
    let tocPageCount = 1; // 目录页数量
    
    if (font) {
      tocPage.drawText('目录', {
        x: 50,
        y: 750,
        size: 24,
        font: font
      });
    } else {
      tocPage.drawText('Table of Contents', {
        x: 50,
        y: 750,
        size: 24
      });
    }
    
    // 读取bookmarks.txt文件来获取层级信息
    let bookmarksData = null;
    const bookmarksPath = path.join(outputDir, 'bookmarks.txt');
    if (fs.existsSync(bookmarksPath)) {
      try {
        const bookmarksContent = fs.readFileSync(bookmarksPath, 'utf8');
        bookmarksData = bookmarksContent.split('\n').filter(line => line.trim() && !line.includes('目录：'));
      } catch (err) {
        console.warn('⚠️ 读取bookmarks.txt失败:', err.message);
      }
    }
    
    // 在目录页添加条目（带层级）
    for (const chapter of chapterInfo) {
      // 检查是否需要新页面（防止内容超出页面）
      if (yPosition < 50) {
        // 创建新页面
        tocPage = mergedPdf.addPage([595, 842]);
        tocPages.push(tocPage);
        tocPageCount++;
        yPosition = 750;
        
        if (font) {
          tocPage.drawText('目录（续）', {
            x: 50,
            y: 780,
            size: 24,
            font: font
          });
        } else {
          tocPage.drawText('Table of Contents (cont.)', {
            x: 50,
            y: 780,
            size: 24
          });
        }
        yPosition -= 50;
      }
      
      // 根据bookmarks.txt确定层级和缩进
      let indent = 0;
      let displayText = `${chapter.index}. ${chapter.text}`;
      
      if (bookmarksData) {
        // 在bookmarks中查找对应的条目
        const bookmarkEntry = bookmarksData.find(line => 
          line.includes(chapter.text) || 
          line.replace(/\s*\(.+页\)$/, '').trim().endsWith(chapter.text)
        );
        
        if (bookmarkEntry) {
          // 计算缩进级别
          const leadingSpaces = bookmarkEntry.length - bookmarkEntry.trimStart().length;
          indent = leadingSpaces / 4; // 每4个空格为一个缩进级别
          
          // 使用bookmarks.txt中的格式
          const formattedText = bookmarkEntry.replace(/\s*\(第\d+页\)$/, '');
          displayText = formattedText.trimStart();
        }
      }
      
      const xPosition = 50 + (indent * 20); // 每级缩进20个单位
      
      if (font) {
        tocPage.drawText(displayText, {
          x: xPosition,
          y: yPosition,
          size: indent > 0 ? 12 : 14, // 子章节使用较小字体
          color: rgb(0, 0, 0.6),
          font: font
        });
      } else {
        // 如果无法加载中文字体，尝试过滤掉中文字符
        const asciiText = displayText.replace(/[\u4e00-\u9fff]/g, '');
        if (asciiText.trim()) {
          tocPage.drawText(asciiText.trim(), {
            x: xPosition,
            y: yPosition,
            size: indent > 0 ? 12 : 14,
            color: rgb(0, 0, 0.6)
          });
        }
      }
      yPosition -= indent > 0 ? 20 : 25; // 子章节行距稍小
    }
    
    // 更新currentPageIndex以考虑目录页数量
    currentPageIndex = 1 + tocPageCount; // 封面(1) + 目录页(n)
    
    // 重新开始处理HTML文件转换
    for (const [index, link] of filesToProcess.entries()) {
      const htmlFile = link.href;
      const htmlPath = path.resolve(srcDir, htmlFile);
      const tempPdfPath = path.join(tempDir, `${index}_${path.basename(htmlFile)}`);
      
      // 显示进度
      const progress = ((index + 1) / filesToProcess.length * 100).toFixed(1);
      console.log(`\n[${progress}%] [${index + 1}/${filesToProcess.length}] 正在转换: ${htmlFile}`);
      
      // 检查文件是否存在
      if (!fs.existsSync(htmlPath)) {
        console.warn(`⚠️ 文件不存在: ${htmlFile}，跳过`);
        failCount++;
        continue;
      }
      
      const page = await context.newPage();
      
      try {
        // 加载HTML文件 - 使用更可靠的文件路径
        const fileUrl = `file://${htmlPath.replace(/\\/g, '/')}`;
        await page.goto(fileUrl, { 
          waitUntil: 'domcontentloaded',
          timeout: 300000
        });
        
        // 添加打印优化样式
        await page.addStyleTag({
          content: `
            @media print {
              /* 移除不需要打印的元素 */
              nav, footer, .header, .toc, .no-print, 
              .navbar, .breadcrumb, .level-previous-next, .page-info,
              .panel, .column.is-3, .is-offset-1, .is-offset-1-widescreen,
              .social-share, #disqus_thread, .page-meta { 
                display: none !important; 
              }
              
              /* 隐藏侧边栏和调整布局 */
              .columns, .column {
                display: block !important;
                width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
              }
              
              /* 确保内容完整显示 */
              pre, code { 
                white-space: pre-wrap !important; 
                page-break-inside: avoid;
              }
              
              /* 优化分页 */
              h1, h2, h3 { 
                page-break-after: avoid; 
              }
              img, table { 
                page-break-inside: avoid; 
              }
              
              /* 增加内容区域 */
              body {
                padding: 0.5cm !important;
              }
              
              /* 确保容器不会限制宽度 */
              .container {
                max-width: none !important;
                width: 100% !important;
                padding: 0 !important;
              }
            }
          `
        });
        
        // 等待所有资源加载
        await page.evaluate(async () => {
          const waitForImages = () => {
            return Promise.all(
              Array.from(document.images)
                .filter(img => !img.complete)
                .map(img => new Promise(resolve => {
                  img.onload = img.onerror = resolve;
                }))
            );
          };
          
          await waitForImages();
          
          // 处理懒加载图片
          document.querySelectorAll('img[data-src]').forEach(img => {
            img.src = img.dataset.src;
          });
          
          await waitForImages();
        });
        
        // 生成单页PDF
        const pdfBuffer = await page.pdf({
          format: 'A4',
          printBackground: true,
          margin: { top: '15mm', right: '10mm', bottom: '15mm', left: '10mm' },
          displayHeaderFooter: true,
          headerTemplate: `<div style="font-size: 10px; width: 100%; text-align: center; padding: 5px; font-family: Arial, sans-serif;">
                            ${link.text.replace(/[\u4e00-\u9fff]/g, '')} - Page <span class="pageNumber"></span>
                          </div>`,
          footerTemplate: `<div style="font-size: 8px; width: 100%; text-align: center; padding: 5px; font-family: Arial, sans-serif;">
                            <span class="pageNumber"></span>/<span class="totalPages"></span>
                          </div>`
        });
        
        // 保存临时PDF
        fs.writeFileSync(tempPdfPath, pdfBuffer);
        
        // 将PDF添加到合并文档
        const tempPdf = await PDFDocument.load(fs.readFileSync(tempPdfPath));
        const pages = await mergedPdf.copyPages(tempPdf, tempPdf.getPageIndices());
        
        // 添加书签
        const startPageIndex = currentPageIndex;
        pages.forEach(page => mergedPdf.addPage(page));
        const endPageIndex = currentPageIndex + pages.length - 1;
        
        // 记录章节的实际起始页码（PDF页码从1开始）
        chapterPageMap.set(link.text, startPageIndex);
        
        // 为当前章节添加书签
        bookmarks.push({
          title: link.text,
          pageIndex: startPageIndex,
          children: []
        });
        
        currentPageIndex += pages.length;
        successCount++;
        console.log(`✓ 成功添加: ${link.text} (第${startPageIndex}-${endPageIndex}页)`);
        
      } catch (error) {
        console.error(`✗ 转换失败 ${htmlFile}: ${error.message}`);
        failCount++;
      } finally {
        await page.close();
      }
      
      // 每处理5个文件后释放内存 - 修复context重新赋值问题
      if (index > 0 && index % 5 === 0) {
        console.log('🔄 释放内存...');
        await context.close();
        context = await browser.newContext();
      }
    }
    
    // 检查是否有成功转换的文件
    if (successCount === 0) {
      throw new Error('没有成功转换任何文件，请检查HTML文件格式');
    }
    
    // 保存最终合并的PDF
    console.log('\n📄 正在生成最终PDF文件...');
    let mergedPdfBytes = await mergedPdf.save();
    
    // 生成基于文档标题和作者的文件名
    const sanitizedTitle = sanitizeFilename(docInfo.title);
    const sanitizedAuthor = sanitizeFilename(docInfo.author);
    const baseFileName = testMode ? 'test_document' : `${sanitizedTitle}_${sanitizedAuthor}`;
    const outputPath = path.join(outputDir, `${baseFileName}.pdf`);
    
    // 先保存基础PDF文件
    fs.writeFileSync(outputPath, mergedPdfBytes);
    console.log(`📄 基础PDF文件已保存: ${path.join('output', path.basename(outputPath))}`);
    
    // 添加书签到PDF
    if (bookmarks.length > 0) {
      try {
        console.log('📖 正在添加书签...');
        mergedPdfBytes = await addBookmarksToPdf(mergedPdfBytes, bookmarks, docInfo);
        console.log('✓ 书签添加成功');
        
        // 调用toc_parser.py生成书签文件
        try {
          const { spawn } = require('child_process');
          const tocParserScript = path.join(currentDir, 'toc_parser.py');
          const testMode = process.argv.includes('--test');
          
          if (fs.existsSync(tocParserScript)) {
            console.log('🐍 正在调用toc_parser.py生成书签文件...');
            
            // 将章节页码映射转换为JSON字符串
            const pageMapObj = {};
            for (const [title, pageIndex] of chapterPageMap) {
              pageMapObj[title] = pageIndex;
            }
            const pageMapJson = JSON.stringify(pageMapObj);
            
            // 根据模式确定参数
            const args = [tocParserScript];
            if (testMode) {
              args.push('--test');
            }
            args.push('--page-map', pageMapJson);
            
            const pythonProcess = spawn('python', args);
            
            pythonProcess.stdout.on('data', (data) => {
              // 尝试用UTF-8解码，如果失败则使用原始输出
              try {
                console.log(data.toString('utf8').trim());
              } catch (e) {
                console.log(data.toString().trim());
              }
            });
            
            pythonProcess.stderr.on('data', (data) => {
              // 尝试用UTF-8解码，如果失败则使用原始输出
              try {
                console.warn(data.toString('utf8').trim());
              } catch (e) {
                console.warn(data.toString().trim());
              }
            });
            
            await new Promise((resolve, reject) => {
              pythonProcess.on('close', (code) => {
                if (code === 0) {
                  console.log('✅ toc_parser.py执行完成，书签文件已生成');
                  
                  // 现在调用add_bookmarks.py来添加书签到PDF
                  try {
                    const addBookmarksScript = path.join(currentDir, 'add_bookmarks.py');
                    const testMode = process.argv.includes('--test');
                    const bookmarkFileName = testMode ? 'output/test_bookmarks.txt' : 'output/bookmarks.txt';
                    const bookmarkFilePath = path.join(currentDir, bookmarkFileName);
                    
                    if (fs.existsSync(addBookmarksScript) && fs.existsSync(bookmarkFilePath)) {
                      console.log('🐍 正在使用add_bookmarks.py添加书签到PDF...');
                      
                      const addBookmarksProcess = spawn('python', [
                        addBookmarksScript,
                        outputPath,
                        bookmarkFilePath
                      ]);
                      
                      addBookmarksProcess.stdout.on('data', (data) => {
                        try {
                          console.log(data.toString('utf8').trim());
                        } catch (e) {
                          console.log(data.toString().trim());
                        }
                      });
                      
                      addBookmarksProcess.stderr.on('data', (data) => {
                        try {
                          console.warn(data.toString('utf8').trim());
                        } catch (e) {
                          console.warn(data.toString().trim());
                        }
                      });
                      
                      addBookmarksProcess.on('close', (addBookmarksCode) => {
                        if (addBookmarksCode === 0) {
                          console.log('✅ 书签已成功添加到PDF');
                          resolve();
                        } else {
                          console.warn('⚠️ 书签添加到PDF失败，但PDF已生成');
                          resolve();
                        }
                      });
                    } else {
                      console.log('ℹ️ 书签文件或add_bookmarks.py不存在，跳过书签添加');
                      resolve();
                    }
                  } catch (addBookmarksError) {
                    console.warn('⚠️ 调用add_bookmarks.py时出错:', addBookmarksError.message);
                    resolve();
                  }
                } else {
                  console.warn('⚠️ toc_parser.py执行失败，但PDF已生成');
                  resolve();
                }
              });
            });
          } else {
            console.log('ℹ️ Python脚本不存在，跳过自动书签添加');
          }
        } catch (pythonError) {
          console.warn('⚠️ Python书签添加出错:', pythonError.message);
        }
      } catch (bookmarkError) {
        console.warn('⚠️ 书签添加失败:', bookmarkError.message);
      }
    }
    
    console.log('\n🎉 转换完成!');
    console.log(`✅ 成功转换: ${successCount} 个文件`);
    if (failCount > 0) {
      console.log(`❌ 失败转换: ${failCount} 个文件`);
    }
    console.log(`📁 最终PDF文件: ${path.join('output', path.basename(outputPath))}`);
    console.log(`📊 总页数: ${mergedPdf.getPageCount()}`);
    console.log(`💾 文件大小: ${(mergedPdfBytes.length / 1024 / 1024).toFixed(2)} MB`);
    
  } catch (error) {
    console.error('\n❌ 程序执行出错:', error.message);
    process.exit(1);
  } finally {
    // 清理资源
    try {
      if (context) {
        await context.close();
      }
      if (browser) {
        await browser.close();
      }
      if (tempDir && fs.existsSync(tempDir)) {
        fs.rmSync(tempDir, { recursive: true, force: true });
        console.log('🧹 临时文件已清理');
      }
    } catch (cleanupError) {
      console.warn('⚠️ 清理资源时出现警告:', cleanupError.message);
    }
  }
})();
