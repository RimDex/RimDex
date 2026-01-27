<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="zh_CN">
<context>
    <name>AcfLogReader</name>
    <message>
        <source>Import ACF Data</source>
        <translation>导入 ACF 数据</translation>
    </message>
    <message>
        <source>Export ACF Data</source>
        <translation>导出 ACF 数据</translation>
    </message>
    <message>
        <source>Export to CSV</source>
        <translation>导出为 CSV</translation>
    </message>
    <message>
        <source>Search:</source>
        <translation>搜索：</translation>
    </message>
    <message>
        <source>All Searchable Columns</source>
        <translation>所有可搜索列</translation>
    </message>
    <message>
        <source>Searches selected column or all searchable columns if set to &apos;All&apos;</source>
        <translation>搜索选定列或所有可搜索列（如果设置为“全部”）</translation>
    </message>
</context>
<context>
    <name>BaseModsPanel</name>
    <message>
        <source>Refresh</source>
        <translation>刷新</translation>
    </message>
    <message>
        <source>SteamCMD</source>
        <translation>SteamCMD</translation>
    </message>
    <message>
        <source>Download with SteamCMD</source>
        <translation>使用SteamCMD下载</translation>
    </message>
    <message>
        <source>Select</source>
        <translation>选择</translation>
    </message>
    <message>
        <source>Select all</source>
        <translation>选择全部</translation>
    </message>
    <message>
        <source>Deselect all</source>
        <translation>取消全选</translation>
    </message>
    <message>
        <source>Steam</source>
        <translation>蒸汽</translation>
    </message>
    <message>
        <source>Subscribe selected</source>
        <translation>订阅已选</translation>
    </message>
    <message>
        <source>Unsubscribe selected</source>
        <translation>取消订阅所选内容</translation>
    </message>
</context>
<context>
    <name>ButtonsMixin</name>
    <message>
        <source>Open Page</source>
        <translation>打开页面</translation>
    </message>
    <message>
        <source>Delete</source>
        <translation>删除</translation>
    </message>
</context>
<context>
    <name>CollectionImport</name>
    <message>
        <source>Add Workshop collection link</source>
        <translation>添加创意工坊合集链接</translation>
    </message>
    <message>
        <source>Invalid Link</source>
        <translation>无效的链接</translation>
    </message>
    <message>
        <source>Invalid Workshop collection link. Please enter a valid Workshop collection link.</source>
        <translation>无效的创意工坊合集链接。请输入有效的合集链接。</translation>
    </message>
    <message>
        <source>Incomplete import</source>
        <translation>导入未完成</translation>
    </message>
    <message>
        <source>{len(failed_mods)} mods could not be imported due to missing package ids. This may happen if you don&apos;t have all the mods downloaded.&lt;br&gt;&lt;br&gt;Try subscribing to the collection first</source>
        <translation>由于缺少包 ID，无法导入 {len(failed_mods)} mod。如果您没有下载所有模组，则可能会发生这种情况。&lt;br&gt;&lt;br&gt;请先尝试订阅该合集</translation>
    </message>
</context>
<context>
    <name>ColumnsMixin</name>
    <message>
        <source>Name</source>
        <translation>姓名</translation>
    </message>
    <message>
        <source>Author</source>
        <translation>作者</translation>
    </message>
    <message>
        <source>Package ID</source>
        <translation>封装ID</translation>
    </message>
    <message>
        <source>Published File Id</source>
        <translation>已发布的文件 ID</translation>
    </message>
    <message>
        <source>Supported Versions</source>
        <translation>支持的版本</translation>
    </message>
    <message>
        <source>Mod Downloaded</source>
        <translation>模组下载</translation>
    </message>
    <message>
        <source>Updated on Workshop</source>
        <translation>研讨会更新</translation>
    </message>
    <message>
        <source>Source</source>
        <translation>来源</translation>
    </message>
    <message>
        <source>Path</source>
        <translation>小路</translation>
    </message>
    <message>
        <source>Workshop Page</source>
        <translation>研讨会页面</translation>
    </message>
</context>
<context>
    <name>CsvExportUtils</name>
    <message>
        <source>Invalid File Path</source>
        <translation>文件路径无效</translation>
    </message>
    <message>
        <source>Export Permission Denied</source>
        <translation>出口许可被拒绝</translation>
    </message>
    <message>
        <source>Export File System Error</source>
        <translation>导出文件系统错误</translation>
    </message>
    <message>
        <source>Export Unknown Error</source>
        <translation>导出未知错误</translation>
    </message>
    <message>
        <source>Export Success</source>
        <translation>导出成功</translation>
    </message>
    <message>
        <source>Successfully exported {count} items to {file_path}</source>
        <translation>已成功将 {count} 个项目导出到 {file_path}</translation>
    </message>
</context>
<context>
    <name>DatabaseBuilder</name>
    <message>
        <source>No PublishedFileIDs</source>
        <translation>没有已发布的FileID</translation>
    </message>
    <message>
        <source>DB Builder query did not return any PublishedFileIDs!</source>
        <translation>DB Builder 查询未返回任何 PublishedFileID！</translation>
    </message>
    <message>
        <source>This is typically caused by invalid/missing Steam WebAPI key, or a connectivity issue to the Steam WebAPI.&lt;br&gt;PublishedFileIDs are needed to retrieve mods from Steam!</source>
        <translation>这通常是由于 Steam WebAPI 密钥无效/丢失或 Steam WebAPI 连接问题造成的。&lt;br&gt;需要 PublishedFileID 才能从 Steam 检索模组！</translation>
    </message>
    <message>
        <source>Are you sure?</source>
        <translation>你确定吗？</translation>
    </message>
    <message>
        <source>Here be dragons.</source>
        <translation>这里有龙。</translation>
    </message>
    <message>
        <source>WARNING: It is NOT recommended to subscribe to this many mods at once via Steam. Steam has limitations in place seemingly intentionally and unintentionally for API subscriptions. It is highly recommended that you instead download these mods to a SteamCMD prefix by using SteamCMD. This can take longer due to rate limits, but you can also re-use the script generated by RimDex with a separate, authenticated instance of SteamCMD, if you do not want to anonymously download via RimDex.</source>
        <translation>警告：不建议通过 Steam 一次性订阅这么多模组。 Steam 对 API 订阅似乎有意无意地设置了限制。强烈建议您使用 SteamCMD 将这些 mod 下载到 SteamCMD 前缀。由于速率限制，这可能需要更长的时间，但如果您不想通过 RimDex 匿名下载，您也可以通过单独的、经过身份验证的 SteamCMD 实例重新使用 RimDex 生成的脚本。</translation>
    </message>
    <message>
        <source>Steam DB Builder</source>
        <translation>Steam 数据库生成器</translation>
    </message>
    <message>
        <source>This operation will compare 2 databases, A &amp; B, by checking dependencies from A with dependencies from B.</source>
        <translation>此操作将通过检查 A 的依赖关系与 B 的依赖关系来比较 2 个数据库 A 和 B。</translation>
    </message>
    <message>
        <source>- This will produce an accurate comparison of dependency data between 2 Steam DBs.&lt;br&gt;A report of discrepancies is generated. You will be prompted for these paths in order:&lt;br&gt;&lt;br&gt;	1) Select input A&lt;br&gt;	2) Select input B</source>
        <translation>- 这将生成 2 个 Steam DB 之间的依赖性数据的准确比较。&lt;br&gt;生成差异报告。系统将按顺序提示您输入这些路径：&lt;br&gt;&lt;br&gt; 1) 选择输入 A&lt;br&gt; 2) 选择输入 B</translation>
    </message>
    <message>
        <source>- This will effectively recursively overwrite A&apos;s key/value with B&apos;s key/value to the resultant database.&lt;br&gt;- Exceptions will not be recursively updated. Instead, they will be overwritten with B&apos;s key entirely.&lt;br&gt;- The following exceptions will be made:&lt;br&gt;&lt;br&gt;	{DB_BUILDER_RECURSE_EXCEPTIONS}&lt;br&gt;&lt;br&gt;The resultant database, C, is saved to a user-specified path. You will be prompted for these paths in order:&lt;br&gt;&lt;br&gt;	1) Select input A (db to-be-updated)&lt;br&gt;	2) Select input B (update source)&lt;br&gt;	3) Select output C (resultant db)</source>
        <translation>- 这将有效地递归地用 B 的键/值覆盖结果数据库中的 A 的键/值。&lt;br&gt;- 异常不会被递归更新。相反，它们将被 B 的密钥完全覆盖。&lt;br&gt;- 将出现以下例外情况：&lt;br&gt;&lt;br&gt; {DB_BUILDER_RECURSE_EXCEPTIONS}&lt;br&gt;&lt;br&gt;生成的数据库 C 将保存到用户指定的路径。系统将按顺序提示您输入这些路径：&lt;br&gt;&lt;br&gt; 1) 选择输入 A（要更新的数据库）&lt;br&gt; 2) 选择输入 B（更新源）&lt;br&gt; 3) 选择输出 C（生成的数据库）</translation>
    </message>
    <message>
        <source>Error: {}</source>
        <translation>错误： {}</translation>
    </message>
    <message>
        <source>Steam DB comparison report: {count} found</source>
        <translation>Steam DB 比较报告：找到 {count} 个</translation>
    </message>
    <message>
        <source>Click &apos;Show Details&apos; to see the full report!</source>
        <translation>点击“显示详细信息”查看完整报告！</translation>
    </message>
    <message>
        <source>This operation will merge 2 databases, A &amp; B, by recursively updating A with B, barring exceptions.</source>
        <translation>此操作将通过递归地用 B 更新 A 来合并 2 个数据库 A 和 B，除非有例外。</translation>
    </message>
    <message>
        <source>Save Error</source>
        <translation>保存错误</translation>
    </message>
    <message>
        <source>Failed to save merged database</source>
        <translation>保存合并数据库失败</translation>
    </message>
</context>
<context>
    <name>DatabaseBuilderDialog</name>
    <message>
        <source>Database Builder</source>
        <translation>数据库生成器</translation>
    </message>
    <message>
        <source>When building the database:</source>
        <translation>建立数据库时：</translation>
    </message>
    <message>
        <source>Get PublishedFileIDs from locally installed mods.</source>
        <translation>从本地安装的 mod 获取 PublishedFileID。</translation>
    </message>
    <message>
        <source>Mods you wish to update must be installed, as the initial DB is built including data from mods&apos; About.xml files.</source>
        <translation>必须安装您想要更新的 Mod，因为构建的初始数据库包括来自 Mod 的 About.xml 文件的数据。</translation>
    </message>
    <message>
        <source>Get PublishedFileIDs from the Steam Workshop.</source>
        <translation>从 Steam 创意工坊获取 PublishedFileID。</translation>
    </message>
    <message>
        <source>Mods to be updated don&apos;t have to be installed, as the initial DB is built by scraping the Steam Workshop.</source>
        <translation>不需要安装要更新的模组，因为初始数据库是通过抓取 Steam 创意工坊构建的。</translation>
    </message>
    <message>
        <source>Query DLC dependency data with Steamworks API</source>
        <translation>使用 Steamworks API 查询 DLC 依赖数据</translation>
    </message>
    <message>
        <source>Update database instead of overwriting</source>
        <translation>更新数据库而不是覆盖</translation>
    </message>
    <message>
        <source>Steam API key:</source>
        <translation>Steam API 密钥：</translation>
    </message>
    <message>
        <source>Download all published Workshop mods via:</source>
        <translation>通过以下方式下载所有已发布的创意工坊模组：</translation>
    </message>
    <message>
        <source>SteamCMD</source>
        <translation>SteamCMD</translation>
    </message>
    <message>
        <source>Steam</source>
        <translation>蒸汽</translation>
    </message>
    <message>
        <source>Compare Databases</source>
        <translation>比较数据库</translation>
    </message>
    <message>
        <source>Merge Databases</source>
        <translation>合并数据库</translation>
    </message>
    <message>
        <source>Build Database</source>
        <translation>建立数据库</translation>
    </message>
</context>
<context>
    <name>DuplicateModsPanel</name>
    <message>
        <source>RimDex - Duplicate Mods Found</source>
        <translation>RimDex - 发现重复模组</translation>
    </message>
    <message>
        <source>Duplicate mods detected!</source>
        <translation>检测到重复的模组！</translation>
    </message>
    <message>
        <source>
The following table displays duplicate mods grouped by package ID. Select which versions to keep and choose an action.</source>
        <translation>下表显示了按包名分组的重复模组。选择要保留的版本并选择操作。</translation>
    </message>
</context>
<context>
    <name>FatalErrorDialog</name>
    <message>
        <source>Show Details</source>
        <translation>显示详情</translation>
    </message>
    <message>
        <source>Close</source>
        <translation>关闭</translation>
    </message>
    <message>
        <source>Open Log Directory</source>
        <translation>打开日志目录</translation>
    </message>
    <message>
        <source>Upload Log</source>
        <translation>上传日志</translation>
    </message>
    <message>
        <source>Upload the log file to 0x0.st</source>
        <translation>将日志文件上传到0x0.st</translation>
    </message>
    <message>
        <source>Hide Details</source>
        <translation>隐藏详情</translation>
    </message>
</context>
<context>
    <name>FileSearchController</name>
    <message>
        <source>Preparing search...</source>
        <translation>正在准备搜索...</translation>
    </message>
    <message>
        <source>Starting new search...</source>
        <translation>正在开始新搜索...</translation>
    </message>
    <message>
        <source>Active Mods Error</source>
        <translation>启用模组错误</translation>
    </message>
    <message>
        <source>No active mods found</source>
        <translation>未找到启用的模组</translation>
    </message>
    <message>
        <source>Inactive Mods Error</source>
        <translation>未启用模组错误</translation>
    </message>
    <message>
        <source>No inactive mods found</source>
        <translation>未找到未启用的模组</translation>
    </message>
    <message>
        <source>Stopping search...</source>
        <translation>正在停止搜索...</translation>
    </message>
    <message>
        <source>Search stopped by user</source>
        <translation>搜索已被用户终止</translation>
    </message>
    <message>
        <source>Regular Expression Error</source>
        <translation>正则表达式错误</translation>
    </message>
    <message>
        <source>There was an error with your regular expression pattern.</source>
        <translation>你的正则表达式有误。</translation>
    </message>
    <message>
        <source>{error_msg}&lt;br&gt;&lt;br&gt;Try simplifying your pattern or check for syntax errors.</source>
        <translation>{error_msg}&lt;br&gt;&lt;br&gt;尝试简化您的模式或检查语法错误。</translation>
    </message>
    <message>
        <source>{error_msg}&lt;br&gt;&lt;br&gt;Try running RimDex with administrator privileges or check folder permissions.</source>
        <translation>{error_msg}&lt;br&gt;&lt;br&gt;尝试使用管理员权限运行 RimDex 或检查文件夹权限。</translation>
    </message>
    <message>
        <source>{error_msg}&lt;br&gt;&lt;br&gt;Try searching in smaller batches or use the &apos;streaming search&apos; method for very large files.</source>
        <translation>{error_msg}&lt;br&gt;&lt;br&gt;尝试小批量搜索或对非常大的文件使用“流式搜索”方法。</translation>
    </message>
    <message>
        <source>{error_msg}&lt;br&gt;&lt;br&gt;Please check your settings and try again.</source>
        <translation>{error_msg}&lt;br&gt;&lt;br&gt;请检查您的设置并重试。</translation>
    </message>
    <message>
        <source>File Access Error</source>
        <translation>文件访问错误</translation>
    </message>
    <message>
        <source>RimDex doesn&apos;t have permission to access some files.</source>
        <translation>RimDex 没有权限访问部分文件。</translation>
    </message>
    <message>
        <source>Memory Error</source>
        <translation>内存错误</translation>
    </message>
    <message>
        <source>RimDex ran out of memory while searching.</source>
        <translation>RimDex 在搜索时内存不足。</translation>
    </message>
    <message>
        <source>Search Error</source>
        <translation>搜索错误</translation>
    </message>
    <message>
        <source>An error occurred during the search.</source>
        <translation>搜索过程中发生错误。</translation>
    </message>
    <message>
        <source>Search failed: {error_msg[:100]}...</source>
        <translation>搜索失败：{error_msg[:100]}...</translation>
    </message>
    <message>
        <source>Filter: {visible_rows} of {rowCount} results visible</source>
        <translation>筛选：{visible_rows} / {rowCount} 个结果可见</translation>
    </message>
    <message>
        <source>Location Not Set</source>
        <translation>路径未设置</translation>
    </message>
    <message>
        <source>No valid search location is available for the selected scope. Please configure your game folders in the settings.</source>
        <translation>在此搜索范围内没有可用的搜索路径。请在设置中配置游戏文件夹。</translation>
    </message>
</context>
<context>
    <name>FileSearchDialog</name>
    <message>
        <source>Search for:</source>
        <translation>搜索内容：</translation>
    </message>
    <message>
        <source>Enter text to search for in files</source>
        <translation>输入要在文件中搜索的文本</translation>
    </message>
    <message>
        <source>Recent Searches</source>
        <translation>最近搜索</translation>
    </message>
    <message>
        <source>Search in:</source>
        <translation>搜索范围：</translation>
    </message>
    <message>
        <source>active mods</source>
        <translation>启用的模组</translation>
    </message>
    <message>
        <source>inactive mods</source>
        <translation>未启用的模组</translation>
    </message>
    <message>
        <source>all mods</source>
        <translation>所有的模组</translation>
    </message>
    <message>
        <source>configs folder</source>
        <translation>配置文件夹</translation>
    </message>
    <message>
        <source>Search Options:</source>
        <translation>搜索选项：</translation>
    </message>
    <message>
        <source>Case sensitive</source>
        <translation>区分大小写</translation>
    </message>
    <message>
        <source>Match exact case when searching</source>
        <translation>搜索时区分大小写</translation>
    </message>
    <message>
        <source>Use regex (pattern search)</source>
        <translation>使用正则表达式</translation>
    </message>
    <message>
        <source>Enable to use regular expressions in search
Examples:
- &apos;def.*\(&apos; to find function definitions
- &apos;&lt;[^&gt;]+&gt;&apos; to find XML tags
- &apos;\d+\.\d+(\.\d+)?&apos; to find version numbers</source>
        <translation>使用正则表达式（模式搜索）
示例：
- &apos;def.*\(&apos; 查找函数定义
- &apos;&lt;[^&gt;]+&gt;&apos; 查找 XML 标签
- &apos;\d+\.\d+(\.\d+)?&apos; 查找版本号</translation>
    </message>
    <message>
        <source>XML files only</source>
        <translation>仅限 XML 文件</translation>
    </message>
    <message>
        <source>When checked, search only XML files and use optimized XML search.
When unchecked, search all file types with standard search.</source>
        <translation>选择时，仅搜索 XML 文件，并使用优化的 XML 搜索方式。
取消选择时，使用标准搜索方式搜索所有文件类型。</translation>
    </message>
    <message>
        <source>Exclude from Search:</source>
        <translation>在搜索中排除：</translation>
    </message>
    <message>
        <source>Skip translations</source>
        <translation>跳过翻译</translation>
    </message>
    <message>
        <source>Skip translation files to improve search speed</source>
        <translation>跳过翻译文件以提高搜索速度</translation>
    </message>
    <message>
        <source>Skip .git folder</source>
        <translation>跳过 .git 文件夹</translation>
    </message>
    <message>
        <source>Skip Git repository folders</source>
        <translation>跳过 Git 仓库文件夹</translation>
    </message>
    <message>
        <source>Skip Source folder</source>
        <translation>跳过 Source 文件夹</translation>
    </message>
    <message>
        <source>Skip Source folders containing C# code</source>
        <translation>跳过包含 C# 代码的 Source 文件夹</translation>
    </message>
    <message>
        <source>Skip Textures folder</source>
        <translation>跳过 Textures 文件夹</translation>
    </message>
    <message>
        <source>Skip Textures folders containing images</source>
        <translation>跳过包含图像的 Textures 文件夹</translation>
    </message>
    <message>
        <source>Search method is automatically selected based on options</source>
        <translation>搜索方法将会根据选项自动处理</translation>
    </message>
    <message>
        <source>Search</source>
        <translation>搜索</translation>
    </message>
    <message>
        <source>Stop</source>
        <translation>暂停</translation>
    </message>
    <message>
        <source>Ready to search</source>
        <translation>准备搜索</translation>
    </message>
    <message>
        <source>Filter results:</source>
        <translation>筛选结果：</translation>
    </message>
    <message>
        <source>Filter results by mod name, file name, or path</source>
        <translation>通过模组名称、文件名或路径过滤结果</translation>
    </message>
    <message>
        <source>Search Results:</source>
        <translation>搜索结果：</translation>
    </message>
    <message>
        <source>Mod Name</source>
        <translation>模组名称</translation>
    </message>
    <message>
        <source>File Name</source>
        <translation>文件名称</translation>
    </message>
    <message>
        <source>Path</source>
        <translation>路径</translation>
    </message>
    <message>
        <source>Preview</source>
        <translation>预览</translation>
    </message>
    <message>
        <source>Found {result_count} results</source>
        <translation>已找到 {result_count} 个结果</translation>
    </message>
    <message>
        <source>No results found</source>
        <translation>未找到结果</translation>
    </message>
    <message>
        <source>Open File (Enter)</source>
        <translation>打开文件（Enter）</translation>
    </message>
    <message>
        <source>Open Containing Folder (Ctrl+O)</source>
        <translation>打开所在文件夹（Ctrl+O）</translation>
    </message>
    <message>
        <source>Copy Path (Ctrl+C)</source>
        <translation>复制路径（Ctrl+C）</translation>
    </message>
    <message>
        <source>Open With...</source>
        <translation>用其他程序打开</translation>
    </message>
    <message>
        <source>Notepad</source>
        <translation>记事本</translation>
    </message>
    <message>
        <source>VS Code</source>
        <translation>VS Code</translation>
    </message>
    <message>
        <source>Default Editor</source>
        <translation>默认编辑器</translation>
    </message>
    <message>
        <source>Clear Recent Searches</source>
        <translation>清除历史记录</translation>
    </message>
    <message>
        <source>Filter: {visible_rows} of {total_rows} results visible</source>
        <translation>筛选：{visible_rows} / {total_rows} 个结果可见</translation>
    </message>
    <message>
        <source>Found {total_rows} results</source>
        <translation>共找到 {total_rows} 个结果</translation>
    </message>
    <message>
        <source>Right-click a result for actions</source>
        <translation>右键单击结果以进行操作</translation>
    </message>
    <message>
        <source>Right-click for actions</source>
        <translation>右键单击以进行操作</translation>
    </message>
</context>
<context>
    <name>GitHubModsPanel</name>
    <message>
        <source>RimDex - GitHub Mods</source>
        <translation>RimDex - GitHub Mods</translation>
    </message>
    <message>
        <source>GitHub Mods</source>
        <translation>GitHub 模组</translation>
    </message>
    <message>
        <source>
Manage mods installed from GitHub releases.</source>
        <translation>管理从 GitHub 版本安装的 mod。</translation>
    </message>
    <message>
        <source>Check for Updates</source>
        <translation>检查更新</translation>
    </message>
    <message>
        <source>Update Selected</source>
        <translation>更新所选内容</translation>
    </message>
    <message>
        <source>Checking for updates...</source>
        <translation>正在检查更新...</translation>
    </message>
    <message>
        <source>{count} update(s) available: {names}{suffix}</source>
        <translation>{count} 个可用更新：{names}{suffix}</translation>
    </message>
    <message>
        <source>All mods are up to date.</source>
        <translation>所有模组都是最新的。</translation>
    </message>
    <message>
        <source>Update check failed: {error}</source>
        <translation>更新检查失败： {error}</translation>
    </message>
</context>
<context>
    <name>IgnoreJsonEditor</name>
    <message>
        <source>RimDex - Manage Ignore List</source>
        <translation>RimDex - 管理忽略列表</translation>
    </message>
    <message>
        <source>No mods in ignore list.</source>
        <translation>忽略列表中没有模组。</translation>
    </message>
    <message>
        <source>Mods checked below will be removed from the ignore list.</source>
        <translation>下面选中的模组将从忽略列表中移除。</translation>
    </message>
    <message>
        <source>Remove Selected</source>
        <translation>移除所选模组</translation>
    </message>
    <message>
        <source>Save</source>
        <translation>保存</translation>
    </message>
    <message>
        <source>Cancel</source>
        <translation>取消</translation>
    </message>
    <message>
        <source>Error</source>
        <translation>错误</translation>
    </message>
    <message>
        <source>Failed to load ignored mods: {}</source>
        <translation>无法加载忽略的模组：{}</translation>
    </message>
    <message>
        <source>Error saving changes: {}</source>
        <translation>保存更改时出错：{}</translation>
    </message>
    <message>
        <source>Success</source>
        <translation>成功</translation>
    </message>
    <message>
        <source>Ignore list has been saved successfully.</source>
        <translation>忽略列表已成功保存。</translation>
    </message>
    <message>
        <source>Failed to save changes to ignore list.</source>
        <translation>保存忽略列表的更改失败。</translation>
    </message>
</context>
<context>
    <name>InstanceController</name>
    <message>
        <source>Invalid archive path</source>
        <translation>无效的存档路径</translation>
    </message>
    <message>
        <source>The provided archive path is invalid.</source>
        <translation>提供的存档路径无效。</translation>
    </message>
    <message>
        <source>Please provide a valid archive path.</source>
        <translation>请提供有效的存档路径。</translation>
    </message>
    <message>
        <source>Error restoring instance</source>
        <translation>恢复实例时出错</translation>
    </message>
    <message>
        <source>An error occurred while reading instance archive: {e}</source>
        <translation>读取实例存档时发生错误：{e}</translation>
    </message>
</context>
<context>
    <name>InstanceService</name>
    <message>
        <source>Essential path(s)</source>
        <translation>基本路径</translation>
    </message>
    <message>
        <source>Essential path(s) are invalid or not set!</source>
        <translation>基本路径无效或未设置！</translation>
    </message>
    <message>
        <source>RimDex requires the below paths to be set.&lt;br/&gt;&lt;br/&gt;1) Game folder (Folder where RimWorld is installed).&lt;br/&gt;&lt;br/&gt;2) Config folder (Folder where ModsConfig.xml is located)&lt;br/&gt;&lt;br/&gt;3) Local mods folder (Mods folder inside the RimWorld installation).&lt;br/&gt;&lt;br/&gt;4) Steam mods folder (Only set if you use Steam user also enable Steam Client Integration)&lt;br/&gt;&lt;br/&gt;Try Using the autodetect functionality to set all paths automatically.&lt;br/&gt;&lt;br/&gt;Would you like to open the settings to configure them now?</source>
        <translation>RimDex 需要设置以下路径。&lt;br/&gt;&lt;br/&gt;1) 游戏文件夹（安装 RimWorld 的文件夹）。&lt;br/&gt;&lt;br/&gt;2) Config 文件夹（ModsConfig.xml 所在的文件夹）&lt;br/&gt;&lt;br/&gt;3) 本地 mods 文件夹（RimWorld 安装中的 Mods 文件夹）。&lt;br/&gt;&lt;br/&gt;4) Steam mods 文件夹（仅当您使用 Steam 用户并启用 Steam 客户端集成时才设置）&lt;br/&gt;&lt;br/&gt;尝试使用自动检测功能自动设置所有路径。&lt;br/&gt;&lt;br/&gt;您想立即打开设置来配置它们吗？</translation>
    </message>
    <message>
        <source>Yes</source>
        <translation>是的</translation>
    </message>
    <message>
        <source>No</source>
        <translation>不</translation>
    </message>
    <message>
        <source>Provide instance name</source>
        <translation>提供实例名称</translation>
    </message>
    <message>
        <source>Input a unique name for the backed up instance that is not &quot;{name}&quot;</source>
        <translation>输入备份实例的唯一名称，该名称不是“{name}”</translation>
    </message>
    <message>
        <source>Invalid name</source>
        <translation>名称无效</translation>
    </message>
    <message>
        <source>&quot;{name}&quot; is not allowed. Please choose a different name.</source>
        <translation>不允许使用“{name}”。请选择不同的名称。</translation>
    </message>
    <message>
        <source>Compressing [{instance_name}] instance folder to archive...</source>
        <translation>正在压缩 [{instance_name}] 实例文件夹以存档...</translation>
    </message>
    <message>
        <source>Error restoring instance</source>
        <translation>恢复实例时出错</translation>
    </message>
    <message>
        <source>Archive not found at path: {input_path}</source>
        <translation>在路径：{input_path} 处找不到存档</translation>
    </message>
    <message>
        <source>An error occurred while reading instance archive: {e}</source>
        <translation>读取实例存档时出错：{e}</translation>
    </message>
    <message>
        <source>Instance folder exists</source>
        <translation>实例文件夹存在</translation>
    </message>
    <message>
        <source>Instance folder already exists: {instance_folder_path}</source>
        <translation>实例文件夹已存在：{instance_folder_path}</translation>
    </message>
    <message>
        <source>Do you want to continue and replace the existing instance folder?</source>
        <translation>您想继续并替换现有实例文件夹吗？</translation>
    </message>
    <message>
        <source>Replace</source>
        <translation>代替</translation>
    </message>
    <message>
        <source>Restoring instance [{name}] from archive...</source>
        <translation>正在从存档中恢复实例 [{name}]...</translation>
    </message>
    <message>
        <source>Invalid instance folder paths</source>
        <translation>实例文件夹路径无效</translation>
    </message>
    <message>
        <source>Some folder paths from the restored instance are invalid and were cleared. Please reconfigure them in the settings</source>
        <translation>恢复的实例中的某些文件夹路径无效并已被清除。请在设置中重新配置它们</translation>
    </message>
    <message>
        <source>Invalid paths: {path}</source>
        <translation>无效路径：{path}</translation>
    </message>
    <message>
        <source>Couldn&apos;t restore steamcmd symlink/junction</source>
        <translation>无法恢复 steamcmd 符号链接/连接</translation>
    </message>
    <message>
        <source>The steamcmd symlink/junction could not be restored as the local folder is not set or invalid. The symlink/junction will need to be manually recreated.</source>
        <translation>由于本地文件夹未设置或无效，无法恢复 steamcmd 符号链接/连接。符号链接/连接需要手动重新创建。</translation>
    </message>
    <message>
        <source>An error occurred while restoring instance [{name}].</source>
        <translation>恢复实例 [{name}] 时发生错误。</translation>
    </message>
    <message>
        <source>The instance folder was not found after extracting the archive. Perhaps the archive is corrupt or the instance name is invalid.</source>
        <translation>解压存档后未找到实例文件夹。也许存档已损坏或实例名称无效。</translation>
    </message>
    <message>
        <source>Create new instance</source>
        <translation>创建新实例</translation>
    </message>
    <message>
        <source>Input a unique name of new instance that is not already used:</source>
        <translation>输入尚未使用的新实例的唯一名称：</translation>
    </message>
    <message>
        <source>Clone instance [{name}]</source>
        <translation>克隆实例 [{name}]</translation>
    </message>
    <message>
        <source>What would you like to do with the configured Workshop mods folder?</source>
        <translation>您想对配置好的 Workshop mods 文件夹做什么？</translation>
    </message>
    <message>
        <source>Workshop folder: {folder}&lt;br&gt;&lt;br&gt;Option 1: Convert to SteamCMD&lt;br&gt;RimDex will copy all Workshop mods to the new instance&apos;s local mods folder, converting them to SteamCMD mods that you can manage inside the new instance. The Workshop folder will be ignored for this instance to prevent duplicate mods.&lt;br&gt;&lt;br&gt;Option 2: Keep Workshop Folder&lt;br&gt;The new instance will use the same Workshop folder as the original instance. You can change this later in the settings if needed.&lt;br&gt;&lt;br&gt;How would you like to proceed?</source>
        <translation>创意工坊文件夹：&lt;br&gt;&lt;br&gt;选项 1：转换为 SteamCMD&lt;br&gt;RimDex 会将所有创意工坊模组复制到新实例的本地模组文件夹，将它们转换为您可以在新实例中管理的 SteamCMD 模组。此实例的创意工坊文件夹将被忽略，以防止重复模组。&lt;br&gt;&lt;br&gt;选项 2：保留创意工坊文件夹&lt;br&gt;新实例将使用与原始实例相同的创意工坊文件夹。如果需要，您可以稍后在设置中更改此设置。&lt;br&gt;&lt;br&gt;您想如何继续？ {folder}</translation>
    </message>
    <message>
        <source>Convert to SteamCMD</source>
        <translation>转换为SteamCMD</translation>
    </message>
    <message>
        <source>Keep Workshop Folder</source>
        <translation>保留创意工坊文件夹</translation>
    </message>
    <message>
        <source>Workshop folder not configured</source>
        <translation>创意工坊文件夹未配置</translation>
    </message>
    <message>
        <source>Workshop folder was not configured for the cloned instance. You can set it later in settings.</source>
        <translation>未为克隆实例配置 Workshop 文件夹。您可以稍后在设置中进行设置。</translation>
    </message>
    <message>
        <source>Workshop mods not found</source>
        <translation>找不到创意工坊模组</translation>
    </message>
    <message>
        <source>Workshop mods folder at [{existing_instance_workshop_folder}] not found.</source>
        <translation>找不到 [{existing_instance_workshop_folder}] 处的创意工坊 mods 文件夹。</translation>
    </message>
    <message>
        <source>Error cloning instance</source>
        <translation>克隆实例时出错</translation>
    </message>
    <message>
        <source>Unable to clone instance.</source>
        <translation>无法克隆实例。</translation>
    </message>
    <message>
        <source>Please enter a valid, unique instance name. It cannot be &apos;{name}&apos; or empty.</source>
        <translation>请输入有效、唯一的实例名称。它不能是“{name}”或为空。</translation>
    </message>
    <message>
        <source>Create new instance [{instance_name}]</source>
        <translation>创建新实例 [{instance_name}]</translation>
    </message>
    <message>
        <source>Would you like to automatically generate run args for the new instance?</source>
        <translation>您想为新实例自动生成运行参数吗？</translation>
    </message>
    <message>
        <source>This will try to generate run args for the new instance based on the configured Game/Config folders.&lt;br&gt;&lt;br&gt;Generated run arguments preview:&lt;br&gt;{preview}</source>
        <translation>这将尝试根据配置的 Game/Config 文件夹为新实例生成运行参数。&lt;br&gt;&lt;br&gt;生成的运行参数预览：&lt;br&gt;{preview}</translation>
    </message>
    <message>
        <source>Error creating instance</source>
        <translation>创建实例时出错</translation>
    </message>
    <message>
        <source>Unable to create new instance.</source>
        <translation>无法创建新实例。</translation>
    </message>
    <message>
        <source>Problem deleting instance</source>
        <translation>删除实例时出现问题</translation>
    </message>
    <message>
        <source>Unable to delete instance {current_instance}.</source>
        <translation>无法删除实例 {current_instance}。</translation>
    </message>
    <message>
        <source>The default instance cannot be deleted.</source>
        <translation>默认实例无法删除。</translation>
    </message>
    <message>
        <source>Error deleting instance</source>
        <translation>删除实例时出错</translation>
    </message>
    <message>
        <source>The selected instance does not exist.</source>
        <translation>所选实例不存在。</translation>
    </message>
    <message>
        <source>Delete instance {current_instance}</source>
        <translation>删除实例 {current_instance}</translation>
    </message>
    <message>
        <source>Are you sure you want to delete the selected instance and all of its data?</source>
        <translation>您确定要删除所选实例及其所有数据吗？</translation>
    </message>
    <message>
        <source>This action cannot be undone.</source>
        <translation>此操作无法撤消。</translation>
    </message>
</context>
<context>
    <name>LanguageController</name>
    <message>
        <source>Language Changed</source>
        <translation>语言已更改</translation>
    </message>
    <message>
        <source>The language has been updated.</source>
        <translation>语言已更新</translation>
    </message>
    <message>
        <source>Restart the application to apply the change. Restart now?</source>
        <translation>需要重启应用程序以应用更改。现在重启吗？</translation>
    </message>
    <message>
        <source>Restart</source>
        <translation>重启</translation>
    </message>
</context>
<context>
    <name>LocationsTabController</name>
    <message>
        <source>Invalid Game Location</source>
        <translation>游戏地点无效</translation>
    </message>
    <message>
        <source>Invalid Config Folder</source>
        <translation>无效的配置文件夹</translation>
    </message>
    <message>
        <source>Invalid Local Mods Folder</source>
        <translation>无效的本地 Mod 文件夹</translation>
    </message>
    <message>
        <source>Clear all locations</source>
        <translation>清除所有位置</translation>
    </message>
    <message>
        <source>Are you sure you want to clear all locations?</source>
        <translation>您确定要清除所有位置吗？</translation>
    </message>
</context>
<context>
    <name>MainContent</name>
    <message>
        <source>Essential path(s)</source>
        <translation>必需路径</translation>
    </message>
    <message>
        <source>Scanning mod sources and populating metadata...</source>
        <translation>正在扫描模组来源，加载数据中...</translation>
    </message>
    <message>
        <source>Metadata not loaded</source>
        <translation>元数据未加载</translation>
    </message>
    <message>
        <source>Mod metadata has not finished loading. Please wait and try again.</source>
        <translation>Mod 元数据尚未完成加载。请等待并重试。</translation>
    </message>
    <message>
        <source>Sorting algorithm not implemented</source>
        <translation>排序算法未实现</translation>
    </message>
    <message>
        <source>The selected sorting algorithm is not implemented</source>
        <translation>所选的排序算法未实现</translation>
    </message>
    <message>
        <source>Could not open directory</source>
        <translation>无法打开目录</translation>
    </message>
    <message>
        <source>{directory_name} path does not exist or is not set.</source>
        <translation>{directory_name} 路径不存在或未设置。</translation>
    </message>
    <message>
        <source>Would you like to set the path now?</source>
        <translation>是否要现在设置路径？</translation>
    </message>
    <message>
        <source>Open settings</source>
        <translation>打开设置</translation>
    </message>
    <message>
        <source>File not found</source>
        <translation>无法找到文件</translation>
    </message>
    <message>
        <source>The file you are trying to upload does not exist.</source>
        <translation>你尝试上传的文件不存在。</translation>
    </message>
    <message>
        <source>File: {path}</source>
        <translation>文件：{path}</translation>
    </message>
    <message>
        <source>Uploading {path.name} to 0x0.st...</source>
        <translation>上传 {path.name} 到 0x0.st...</translation>
    </message>
    <message>
        <source>Uploaded file</source>
        <translation>上传文件</translation>
    </message>
    <message>
        <source>Failed to upload file.</source>
        <translation>上传文件失败</translation>
    </message>
    <message>
        <source>Failed to upload the file to 0x0.st</source>
        <translation>无法将文件上传到 0x0.st</translation>
    </message>
    <message>
        <source>Could not save active mods</source>
        <translation>无法保存启用模组</translation>
    </message>
    <message>
        <source>Failed to save active mods to file:</source>
        <translation>无法将启用模组保存到文件：</translation>
    </message>
    <message>
        <source>Confirm texture deletion</source>
        <translation>确认纹理删除</translation>
    </message>
    <message>
        <source>This will delete all optimized .dds textures from your active mods</source>
        <translation>这将从您的活动模组中删除所有优化的 .dds 纹理</translation>
    </message>
    <message>
        <source>Are you sure you want to delete all .dds textures? You can re-optimize them later if needed.</source>
        <translation>您确定要删除所有 .dds 纹理吗？如果需要，您可以稍后重新优化它们。</translation>
    </message>
    <message>
        <source>Delete textures</source>
        <translation>删除纹理</translation>
    </message>
    <message>
        <source>No valid paths for todds</source>
        <translation>todds 没有有效路径</translation>
    </message>
    <message>
        <source>todds could not find any valid mod folders to process.</source>
        <translation>todds 找不到任何有效的 mod 文件夹来处理。</translation>
    </message>
    <message>
        <source>Steam Client Integration is disabled</source>
        <translation>Steam 客户端集成已禁用</translation>
    </message>
    <message>
        <source>This operation will overwrite the {rules_source} database located at the following path:&lt;br&gt;&lt;br&gt;{path}</source>
        <translation>此操作将覆盖位于以下路径的 {rules_source} 数据库：&lt;br&gt;&lt;br&gt;{path}</translation>
    </message>
    <message>
        <source>todds Optimization Failed</source>
        <translation>todds 优化失败</translation>
    </message>
    <message>
        <source>todds texture optimization failed (exit code: {exit_code}), but the game will launch anyway.</source>
        <translation>todds 纹理优化失败（退出代码：{exit_code}），但游戏仍会启动。</translation>
    </message>
    <message>
        <source>Steam protocol launch requires Steam Client Integration to be enabled.</source>
        <translation>Steam 协议启动需要启用 Steam 客户端集成。</translation>
    </message>
    <message>
        <source>Please enable Steam Client Integration in Settings → Steam to use this feature.</source>
        <translation>请在“设置”→“Steam”中启用“Steam 客户端集成”才能使用此功能。</translation>
    </message>
    <message>
        <source>Please configure &quot;Use This Instead&quot; database in settings.</source>
        <translation>请在设置中配置“使用此替代”数据库。</translation>
    </message>
    <message>
        <source>No suggestions were found in the &quot;Use This Instead&quot; database.</source>
        <translation>在 &quot;替代为此&quot; 数据库中没有找到任何建议。</translation>
    </message>
    <message>
        <source>Essential path(s) are invalid or not set!</source>
        <translation>基本路径无效或未设置！</translation>
    </message>
    <message>
        <source>RimDex requires the below paths to be set.&lt;br/&gt;&lt;br/&gt;1) Game folder (Folder where RimWorld is installed).&lt;br/&gt;&lt;br/&gt;2) Config folder (Folder where ModsConfig.xml is located)&lt;br/&gt;&lt;br/&gt;3) Local mods folder (Mods folder inside the RimWorld installation).&lt;br/&gt;&lt;br/&gt;4) Steam mods folder (Only set if you use Steam user also enable Steam Client Integration)&lt;br/&gt;&lt;br/&gt;Try Using the autodetect functionality to set all paths automatically.&lt;br/&gt;&lt;br/&gt;Would you like to open the settings to configure them now?</source>
        <translation>RimDex 需要设置以下路径。&lt;br/&gt;&lt;br/&gt;1) 游戏文件夹（安装 RimWorld 的文件夹）。&lt;br/&gt;&lt;br/&gt;2) Config 文件夹（ModsConfig.xml 所在的文件夹）&lt;br/&gt;&lt;br/&gt;3) 本地 mods 文件夹（RimWorld 安装中的 Mods 文件夹）。&lt;br/&gt;&lt;br/&gt;4) Steam mods 文件夹（仅在使用 Steam 用户并启用 Steam 客户端时设置）集成）&lt;br/&gt;&lt;br/&gt;尝试使用自动检测功能自动设置所有路径。&lt;br/&gt;&lt;br/&gt;您想立即打开设置来配置它们吗？</translation>
    </message>
    <message>
        <source>This may be caused by malformed settings or improper migration between versions or different mod manager.&lt;br&gt;&lt;br&gt;Try resetting your settings, selecting a different sorting algorithm, or deleting your settings file.&lt;br&gt;&lt;br&gt;If the issue persists, please report it to the developers.</source>
        <translation>这可能是由于格式错误的设置或版本或不同模组管理器之间的迁移不当造成的。&lt;br&gt;&lt;br&gt;尝试重置您的设置、选择不同的排序算法或删除您的设置文件。&lt;br&gt;&lt;br&gt;如果问题仍然存在，请将其报告给开发人员。</translation>
    </message>
    <message>
        <source>The URL has been copied to your clipboard:&lt;br&gt;&lt;br&gt;{ret}</source>
        <translation>该网址已复制到您的剪贴板：&lt;br&gt;&lt;br&gt;{ret}</translation>
    </message>
    <message>
        <source>None of the configured mod folder paths exist on disk.&lt;br&gt;&lt;br&gt;Please verify your Local Mods and Workshop folders are correctly set in Settings, then try again.</source>
        <translation>磁盘上不存在已配置的 Mod 文件夹路径。&lt;br&gt;&lt;br&gt;请验证您的本地 Mod 和创意工坊文件夹是否在“设置”中正确设置，然后重试。</translation>
    </message>
    <message>
        <source>Edit Steam DB repo</source>
        <translation>编辑 Steam 数据库仓库</translation>
    </message>
    <message>
        <source>Enter URL (https://github.com/AccountName/RepositoryName):</source>
        <translation>输入 URL (https://github.com/AccountName/RepositoryName):</translation>
    </message>
    <message>
        <source>Edit Community Rules DB repo</source>
        <translation>编辑 社区规则 数据库仓库</translation>
    </message>
    <message>
        <source>Edit Steam WebAPI key</source>
        <translation>编辑 Steam WebAPI key</translation>
    </message>
    <message>
        <source>Enter your personal 32 character Steam WebAPI key here:</source>
        <translation>输入你的个人 32 字符 Steam WebAPI key：</translation>
    </message>
    <message>
        <source>Failed to read existing database</source>
        <translation>读取现有数据库失败</translation>
    </message>
    <message>
        <source>Failed to read the existing database!</source>
        <translation>无法读取现有数据库！</translation>
    </message>
    <message>
        <source>Path: {path}</source>
        <translation>路径：{path}</translation>
    </message>
    <message>
        <source>RimDex - DB Builder</source>
        <translation>RimDex - 数据库构建器</translation>
    </message>
    <message>
        <source>Do you want to continue?</source>
        <translation>你想要继续吗？</translation>
    </message>
    <message>
        <source>Edit SteamDB expiry:</source>
        <translation>编辑 SteamDB 有效期：</translation>
    </message>
    <message>
        <source>Enter your preferred expiry duration in seconds (default 1 week/604800 sec):</source>
        <translation>输入你喜欢的有效期（默认 1 周/604800 秒）：</translation>
    </message>
    <message>
        <source>Tried configuring Dynamic Query with a value that is not an integer.</source>
        <translation>尝试使用不是整数的值配置动态查询。</translation>
    </message>
    <message>
        <source>Please reconfigure the expiry value with an integer in terms of the seconds from epoch you would like your query to expire.</source>
        <translation>请重新配置有效期值，以秒为单位，表示你希望查询过期的时间。</translation>
    </message>
    <message>
        <source>You may experience longer loading times or higher memory usage.&lt;br&gt;&lt;br&gt;Check the todds output window for details.</source>
        <translation>您可能会遇到更长的加载时间或更高的内存使用量。&lt;br&gt;&lt;br&gt;检查 todds 输出窗口以了解详细信息。</translation>
    </message>
    <message>
        <source>Use This Instead</source>
        <translation>替代为此</translation>
    </message>
    <message>
        <source>Unsaved Changes</source>
        <translation>未保存的更改</translation>
    </message>
    <message>
        <source>You have unsaved changes. What would you like to do?</source>
        <translation>你有尚未保存的更改。你想要怎么做？</translation>
    </message>
    <message>
        <source>Save and Run</source>
        <translation>保存并运行</translation>
    </message>
    <message>
        <source>Run Anyway</source>
        <translation>仍然运行</translation>
    </message>
    <message>
        <source>Uploaded {path.name} to https://0x0.st/</source>
        <translation>已将 {path.name} 上传到 https://0x0.st/</translation>
    </message>
    <message>
        <source>Failed to open file.</source>
        <translation>无法打开文件。</translation>
    </message>
    <message>
        <source>Failed to open the file with default text editor. It may not exist.</source>
        <translation>无法使用默认文本编辑器打开文件。文件可能不存在。</translation>
    </message>
</context>
<context>
    <name>MainWindow</name>
    <message>
        <source>Refresh</source>
        <translation>刷新</translation>
    </message>
    <message>
        <source>Clear</source>
        <translation>清空</translation>
    </message>
    <message>
        <source>Restore</source>
        <translation>恢复</translation>
    </message>
    <message>
        <source>Sort</source>
        <translation>排序</translation>
    </message>
    <message>
        <source>Save</source>
        <translation>保存</translation>
    </message>
    <message>
        <source>Run</source>
        <translation>运行</translation>
    </message>
    <message>
        <source>Main Content</source>
        <translation>主界面</translation>
    </message>
    <message>
        <source>File Search</source>
        <translation>文件搜索</translation>
    </message>
    <message>
        <source>Troubleshooting</source>
        <translation>故障排除</translation>
    </message>
    <message>
        <source>Steam Client Integration</source>
        <translation>Steam 客户端集成</translation>
    </message>
    <message>
        <source>&lt;h3&gt;Would you like to enable Steam Client Integration for this instance?&lt;/h3&gt;</source>
        <translation>&lt;h3&gt;你是否希望为此实例启用 Steam 客户端集成？&lt;/h3&gt;</translation>
    </message>
    <message>
        <source>ACF Log Reader</source>
        <translation>更新日志</translation>
    </message>
    <message>
        <source>This will allow you to use RimDex features that require the Steam Client. This includes, among other things, unsubscribing from workshop mods and opening workshop links via the Steam Client. 
                &lt;br&gt;&lt;br&gt;
                You can change this in the settings under the Advanced tab.</source>
        <translation>这将允许你使用需要 Steam 客户端的 RimDex 功能。这包括但不限于通过 Steam 客户端取消订阅创意工坊模组和打开创意工坊链接。
                &lt;br&gt;&lt;br&gt;
                你可以在设置的高级选项卡中更改此设置。</translation>
    </message>
    <message>
        <source>Player Log</source>
        <translation>游戏日志</translation>
    </message>
</context>
<context>
    <name>MenuBar</name>
    <message>
        <source>File</source>
        <translation>文件</translation>
    </message>
    <message>
        <source>Open Mod List…</source>
        <translation>打开模组列表</translation>
    </message>
    <message>
        <source>Save Mod List As…</source>
        <translation>保存模组列表</translation>
    </message>
    <message>
        <source>Import</source>
        <translation>导入</translation>
    </message>
    <message>
        <source>To Rentry.co…</source>
        <translation>导出到 Rentry.co</translation>
    </message>
    <message>
        <source>RimDex</source>
        <translation>RimDex</translation>
    </message>
    <message>
        <source>RimWorld</source>
        <translation>RimWorld</translation>
    </message>
    <message>
        <source>Root Directory</source>
        <translation>根目录</translation>
    </message>
    <message>
        <source>Config Directory</source>
        <translation>配置目录</translation>
    </message>
    <message>
        <source>From Rentry.co</source>
        <translation>从 Rentry.co 导入</translation>
    </message>
    <message>
        <source>From Workshop collection</source>
        <translation>从 创意工坊合集 导入</translation>
    </message>
    <message>
        <source>Export</source>
        <translation>导出</translation>
    </message>
    <message>
        <source>To Clipboard…</source>
        <translation>导出到 剪切板</translation>
    </message>
    <message>
        <source>Upload Log</source>
        <translation>上传日志</translation>
    </message>
    <message>
        <source>Open Log in Default Editor</source>
        <translation>在默认编辑器中打开登录</translation>
    </message>
    <message>
        <source>Open...</source>
        <translation>打开</translation>
    </message>
    <message>
        <source>Logs Directory</source>
        <translation>日志目录</translation>
    </message>
    <message>
        <source>Local Mods Directory</source>
        <translation>本地模组目录</translation>
    </message>
    <message>
        <source>Steam Mods Directory</source>
        <translation>Steam 模组目录</translation>
    </message>
    <message>
        <source>Settings…</source>
        <translation>设置</translation>
    </message>
    <message>
        <source>Exit</source>
        <translation>退出</translation>
    </message>
    <message>
        <source>Edit</source>
        <translation>编辑</translation>
    </message>
    <message>
        <source>Cut</source>
        <translation>剪切</translation>
    </message>
    <message>
        <source>Copy</source>
        <translation>复制</translation>
    </message>
    <message>
        <source>Paste</source>
        <translation>粘贴</translation>
    </message>
    <message>
        <source>Rule Editor…</source>
        <translation>规则编辑器</translation>
    </message>
    <message>
        <source>Ignore JSON Editor…</source>
        <translation>忽略编辑器</translation>
    </message>
    <message>
        <source>Auto-add Translations</source>
        <translation>自动添加翻译</translation>
    </message>
    <message>
        <source>View</source>
        <translation>看法</translation>
    </message>
    <message>
        <source>Show Translation Status</source>
        <translation>显示翻译状态</translation>
    </message>
    <message>
        <source>Download</source>
        <translation>下载</translation>
    </message>
    <message>
        <source>Add Git Mod</source>
        <translation>添加 Git 模组</translation>
    </message>
    <message>
        <source>Add Zip Mod</source>
        <translation>添加 Zip 模组</translation>
    </message>
    <message>
        <source>Browse Workshop</source>
        <translation>浏览创意工坊</translation>
    </message>
    <message>
        <source>Update Workshop Mods</source>
        <translation>更新创意工坊模组</translation>
    </message>
    <message>
        <source>GitHub Mods</source>
        <translation>GitHub 模组</translation>
    </message>
    <message>
        <source>Verify Game Files</source>
        <translation>验证游戏文件</translation>
    </message>
    <message>
        <source>Instances</source>
        <translation>实例</translation>
    </message>
    <message>
        <source>Current: &quot;Default&quot;</source>
        <translation>当前：默认</translation>
    </message>
    <message>
        <source>Backup Instance…</source>
        <translation>备份实例</translation>
    </message>
    <message>
        <source>Restore Instance…</source>
        <translation>恢复实例</translation>
    </message>
    <message>
        <source>Clone Instance…</source>
        <translation>克隆实例</translation>
    </message>
    <message>
        <source>Create Instance…</source>
        <translation>创建实例</translation>
    </message>
    <message>
        <source>Delete Instance…</source>
        <translation>删除实例</translation>
    </message>
    <message>
        <source>Textures</source>
        <translation>纹理</translation>
    </message>
    <message>
        <source>Optimize Textures</source>
        <translation>优化纹理</translation>
    </message>
    <message>
        <source>Delete .dds Textures</source>
        <translation>删除 .dds 纹理</translation>
    </message>
    <message>
        <source>Update</source>
        <translation>更新</translation>
    </message>
    <message>
        <source>Tools</source>
        <translation>工具</translation>
    </message>
    <message>
        <source>Database Builder…</source>
        <translation>数据库生成器...</translation>
    </message>
    <message>
        <source>Translation Manager…</source>
        <translation>翻译经理...</translation>
    </message>
    <message>
        <source>RimDex Wiki…</source>
        <translation>RimDex Wiki</translation>
    </message>
    <message>
        <source>Check for Updates…</source>
        <translation>检查更新</translation>
    </message>
    <message>
        <source>Reset Warning Toggles</source>
        <translation>重置警告状态</translation>
    </message>
    <message>
        <source>Check for Updates on Startup</source>
        <translation>启动时检查更新</translation>
    </message>
    <message>
        <source>Help</source>
        <translation>帮助</translation>
    </message>
    <message>
        <source>RimDex GitHub…</source>
        <translation>RimDex GitHub</translation>
    </message>
    <message>
        <source>From Save file…</source>
        <translation>从 游戏存档导入</translation>
    </message>
    <message>
        <source>Reset Mod Colors</source>
        <translation>重置模组颜色</translation>
    </message>
</context>
<context>
    <name>MenuBarController</name>
    <message>
        <source>Current: {current_instance}</source>
        <translation>当前：{current_instance}</translation>
    </message>
</context>
<context>
    <name>MissingDependenciesDialog</name>
    <message>
        <source>Showing dependencies of your active mods.
Select which missing dependencies to add to your active mods list.</source>
        <translation>显示您的活动模组的依赖关系。
选择要添加到活动 mod 列表中的缺少的依赖项。</translation>
    </message>
    <message>
        <source>Select All</source>
        <translation>全选</translation>
    </message>
    <message>
        <source>Add Selected &amp;&amp; Sort</source>
        <translation>添加并排序</translation>
    </message>
    <message>
        <source>Sort Without Adding</source>
        <translation>仅排序</translation>
    </message>
    <message>
        <source>No dependencies found for any active mod.</source>
        <translation>未找到任何活动模组的依赖项。</translation>
    </message>
    <message>
        <source>&lt;b&gt;Summary:&lt;/b&gt; {total_deps} total dependencies across {mods_with_deps} mods — ✅ {total_satisfied} fulfilled, ⚠️ {total_missing} missing ({total_local} local, {total_download} download) across {total_missing_per_mod} mod(s)</source>
        <translation>&lt;b&gt;摘要：&lt;/b&gt; {mods_with_deps} 个 mod 中的总依赖项为 {total_deps} — ✅ {total_satisfied} 已满足，⚠️ {total_missing} 缺少（{total_local} 本地，{total_download} 下载）（{total_missing_per_mod} 个 mod）</translation>
    </message>
    <message>
        <source>&lt;b&gt;Summary:&lt;/b&gt; {total_deps} total dependencies across {mods_with_deps} mods — ✅ All {total_satisfied} dependencies fulfilled</source>
        <translation>&lt;b&gt;摘要：&lt;/b&gt; {mods_with_deps} mods 中的总依赖项为 {total_deps} — ✅ 满足所有 {total_satisfied} 依赖项</translation>
    </message>
    <message>
        <source>  ✅ Satisfied: </source>
        <translation>✅ 满意：</translation>
    </message>
    <message>
        <source>Available locally - add to active list</source>
        <translation>本地可用 - 添加到活动列表</translation>
    </message>
    <message>
        <source>Needs to be downloaded - requires SteamCMD</source>
        <translation>需要下载 - 需要SteamCMD</translation>
    </message>
    <message>
        <source>
All dependencies are satisfied. No missing dependencies found.</source>
        <translation>所有依赖关系均得到满足。没有发现缺失的依赖项。</translation>
    </message>
    <message>
        <source>Dependency Manager</source>
        <translation>依赖管理</translation>
    </message>
</context>
<context>
    <name>MissingModPropertiesPanel</name>
    <message>
        <source>RimDex - Mods with Missing Properties</source>
        <translation>RimDex - 缺少属性的模组</translation>
    </message>
    <message>
        <source>Mods with Missing Properties detected!</source>
        <translation>检测到缺少属性的模组！</translation>
    </message>
    <message>
        <source>The following mods are missing important properties that may cause issues:

• Missing Package ID: Mods without a valid Package ID in About.xml may have dependency and compatibility issues.
• Missing Publish Field ID: Workshop mods without a Publish Field ID may not support redownloads and update checking.

Please contact the mod authors to add these properties to their mods.</source>
        <translation>以下模组缺少重要属性，可能会导致问题：

• 缺少包名：About.xml 中没有有效包名的模组可能会有依赖性和兼容性问题。
• 缺少发布文件 ID：没有发布文件 ID 的创意工坊模组可能不支持重新下载和更新检查。

请联系模组作者将这些属性添加到他们的模组中。</translation>
    </message>
    <message>
        <source>Add to Ignore List</source>
        <translation>添加到忽略列表</translation>
    </message>
    <message>
        <source>No Selection</source>
        <translation>无选择</translation>
    </message>
    <message>
        <source>Please select mods to add to the ignore list.</source>
        <translation>请选择要添加到忽略列表中的模组。</translation>
    </message>
    <message>
        <source>Error</source>
        <translation>错误</translation>
    </message>
    <message>
        <source>Failed to add mods to ignore list.</source>
        <translation>无法将 mod 添加到忽略列表。</translation>
    </message>
    <message>
        <source>Success</source>
        <translation>成功</translation>
    </message>
    <message>
        <source>Mods added to ignore list. Panel will refresh.</source>
        <translation>Mods 添加到忽略列表。面板将刷新。</translation>
    </message>
    <message>
        <source>Cannot add mods with missing Package IDs to the ignore list.
These mods need valid Package IDs first:
</source>
        <translation>无法将缺少软件包 ID 的模组添加到忽略列表中。
这些 mod 首先需要有效的包 ID：</translation>
    </message>
    <message>
        <source>Cannot Add</source>
        <translation>无法添加</translation>
    </message>
    <message>
        <source>Could not extract package IDs from selected mods.</source>
        <translation>无法从选定的 mod 中提取包 ID。</translation>
    </message>
</context>
<context>
    <name>MissingModsPrompt</name>
    <message>
        <source>RimDex - Missing mods found</source>
        <translation>RimDex - 找到缺失的模组</translation>
    </message>
    <message>
        <source>There are mods missing from the active mods list!</source>
        <translation>启用模组列表中缺少一些模组</translation>
    </message>
    <message>
        <source>Name</source>
        <translation>姓名</translation>
    </message>
    <message>
        <source>Package ID</source>
        <translation>封装ID</translation>
    </message>
    <message>
        <source>Supported Versions</source>
        <translation>支持的版本</translation>
    </message>
    <message>
        <source># Variants</source>
        <translation># 版本</translation>
    </message>
    <message>
        <source>Published File Id</source>
        <translation>已发布的文件 ID</translation>
    </message>
    <message>
        <source>Workshop Page</source>
        <translation>研讨会页面</translation>
    </message>
    <message>
        <source>Download with SteamCMD</source>
        <translation>使用 SteamCMD 下载</translation>
    </message>
    <message>
        <source>Download with Steam client</source>
        <translation>使用 Steam 客户端下载</translation>
    </message>
    <message>
        <source>
User-configured SteamDB database was queried. The following table displays mods available for download from Steam. 

Rimworld mods on Steam Workshop that share a packageId are &quot;variants&quot;. Please keep this in mind before downloading. 

Please select your preferred mod variant in the table below. You can also open each variant in Steam/Web browser to verify.</source>
        <translation>
已查询用户配置的 SteamDB 数据库。下表显示了可以从 Steam 下载的模组。

Steam Workshop 上的 RimWorld 模组如果共享相同的 包名，则为 &apos;变体&apos;。在下载之前，请注意这一点。

请选择你在下表中偏好的 模组变体。你也可以在 Steam 或网页浏览器中打开每个变体进行验证。&quot;</translation>
    </message>
</context>
<context>
    <name>ModDeletionMenu</name>
    <message>
        <source>Delete optimized textures (.dds files only)</source>
        <translation>删除纹理（删除 .dds 纹理）</translation>
    </message>
    <message>
        <source>Mod directory was not empty. Please close all programs accessing files or subfolders in the directory (including your file manager) and try again.</source>
        <translation>模组目录不为空。请关闭所有访问文件或子文件夹的程序（包括你的文件管理器）并重试。</translation>
    </message>
    <message>
        <source>Unable to delete mod</source>
        <translation>无法删除模组</translation>
    </message>
    <message>
        <source>Delete mod completely</source>
        <translation>删除模组</translation>
    </message>
    <message>
        <source>Delete mod (keep .dds textures)</source>
        <translation>删除模组（保留 .dds 纹理）</translation>
    </message>
    <message>
        <source>Delete mod and unsubscribe from Steam</source>
        <translation>删除模组并使用 Steam 取消订阅</translation>
    </message>
    <message>
        <source>Delete mod and resubscribe using Steam</source>
        <translation>删除模组并使用 Steam 重新订阅</translation>
    </message>
    <message>
        <source>An OS error occurred while deleting the mod.</source>
        <translation>删除模组时发生操作系统错误。</translation>
    </message>
    <message>
        <source>No mods selected</source>
        <translation>未选择任何模组</translation>
    </message>
    <message>
        <source>Confirm Complete Deletion</source>
        <translation>确认完全删除</translation>
    </message>
    <message>
        <source>Please select at least one mod to process.</source>
        <translation>请至少选择一个模组进行处理。</translation>
    </message>
    <message>
        <source>Confirm DDS Deletion</source>
        <translation>确认删除 DDS 纹理</translation>
    </message>
    <message>
        <source>Confirm Selective Deletion</source>
        <translation>确认选择删除</translation>
    </message>
    <message>
        <source>An error occurred while trying to {action} from Steam Workshop mods.</source>
        <translation>尝试从 Steam Workshop 模组中 {action} 时发生错误。</translation>
    </message>
    <message>
        <source>Deletion options</source>
        <translation>删除选项</translation>
    </message>
    <message>
        <source>RimSort</source>
        <translation>边缘排序</translation>
    </message>
    <message>
        <source>You have selected {len(selected_mods)} mod(s) for complete deletion.</source>
        <translation>您已选择 mods)进行完全删除。 {len(selected_mods)}</translation>
    </message>
    <message>
        <source>You have selected {len(selected_mods)} mod(s) for DDS texture deletion.</source>
        <translation>您已选择 {len(selected_mods)} mod(s) 进行 DDS 纹理删除。</translation>
    </message>
    <message>
        <source>You have selected {len(selected_mods)} mod(s) for selective deletion.</source>
        <translation>您已选择 {len(selected_mods)} mod(s) 进行选择性删除。</translation>
    </message>
    <message>
        <source>Steam {action}</source>
        <translation>Steam {action}</translation>
    </message>
    <message>
        <source>{action} Error</source>
        <translation>{action} 错误</translation>
    </message>
    <message>
        <source>unsubscribe</source>
        <translation>取消订阅</translation>
    </message>
    <message>
        <source>resubscribe</source>
        <translation>重新订阅</translation>
    </message>
    <message>
        <source>unsubscribed</source>
        <translation>已取消订阅</translation>
    </message>
    <message>
        <source>resubscribed</source>
        <translation>已重新订阅</translation>
    </message>
    <message>
        <source>Successfully deleted {result.success_count} selected mods.</source>
        <translation>成功删除 {result.success_count} 个选定的模组。</translation>
    </message>
    <message>
        <source>Deletion Incomplete</source>
        <translation>删除未完成</translation>
    </message>
    <message>
        <source>Failed to delete {result.failed_count} mod(s). Check logs for details.</source>
        <translation>无法删除 {result.failed_count} 个模组。检查日志以获取详细信息。</translation>
    </message>
    <message>
        <source>{e.strerror or &apos;Unknown error&apos;} occurred at {e.filename or mod_path} with error code {error_code}.</source>
        <translation>在 {e.filename or mod_path} 处发生 {e.strerror or &apos;Unknown error&apos;}，错误代码为 {error_code}。</translation>
    </message>
    <message>
        <source>&lt;br&gt;This operation will permanently delete the selected mod directories from the filesystem.&lt;br&gt;&lt;br&gt;Do you want to proceed?</source>
        <translation>&lt;br&gt;此操作将从文件系统中永久删除选定的 mod 目录。&lt;br&gt;&lt;br&gt;您想继续吗？</translation>
    </message>
    <message>
        <source>&lt;br&gt;This operation will only delete optimized textures (.dds files) from the selected mods.&lt;br&gt;&lt;br&gt;Do you want to proceed?</source>
        <translation>&lt;br&gt;此操作只会从选定的模组中删除优化的纹理（.dds 文件）。&lt;br&gt;&lt;br&gt;您想继续吗？</translation>
    </message>
    <message>
        <source>&lt;br&gt;This operation will delete all mod files except for .dds texture files.&lt;br&gt;The .dds files will be preserved.&lt;br&gt;&lt;br&gt;Do you want to proceed?</source>
        <translation>&lt;br&gt;此操作将删除除 .dds 纹理文件之外的所有 Mod 文件。&lt;br&gt;.dds 文件将被保留。&lt;br&gt;&lt;br&gt;您想继续吗？</translation>
    </message>
    <message>
        <source>Unsubscribe</source>
        <translation>退订</translation>
    </message>
    <message>
        <source>Resubscribe</source>
        <translation>重新订阅</translation>
    </message>
    <message>
        <source>Successfully initiated {action} from {len} Steam Workshop mod(s).&lt;br&gt;The process may take a few moments to complete.</source>
        <translation>已从 {len} 个 Steam 创意工坊模组成功启动 {action}。&lt;br&gt;该过程可能需要一些时间才能完成。</translation>
    </message>
    <message>
        <source>Confirm Deletion and {}</source>
        <translation>确认删除并{}</translation>
    </message>
    <message>
        <source>You have selected {} mod(s) for deletion.&lt;br&gt;{} of these are Steam Workshop mods that will also be {}.</source>
        <translation>您已选择要删除的 {} 个模组。&lt;br&gt;{} 其中是 Steam 创意工坊模组，也将是 {}。</translation>
    </message>
    <message>
        <source>&lt;br&gt;This operation will:&lt;br&gt;• Delete the selected mod directories from your filesystem&lt;br&gt;• {} Steam Workshop mods from your Steam account&lt;br&gt;&lt;br&gt;Do you want to proceed?</source>
        <translation>&lt;br&gt;此操作将：&lt;br&gt;• 从您的文件系统中删除选定的模组目录&lt;br&gt;• 从您的 Steam 帐户中删除 {} 个 Steam 创意工坊模组&lt;br&gt;&lt;br&gt;您想继续吗？</translation>
    </message>
</context>
<context>
    <name>ModInfo</name>
    <message>
        <source>Name:</source>
        <translation>姓名：</translation>
    </message>
    <message>
        <source>Summary:</source>
        <translation>概括：</translation>
    </message>
    <message>
        <source>PackageID:</source>
        <translation>包裹ID:</translation>
    </message>
    <message>
        <source>Authors:</source>
        <translation>作者：</translation>
    </message>
    <message>
        <source>Tags:</source>
        <translation>标签：</translation>
    </message>
    <message>
        <source>Color:</source>
        <translation>颜色：</translation>
    </message>
    <message>
        <source>Mod Version:</source>
        <translation>模组版本：</translation>
    </message>
    <message>
        <source>Supported Version:</source>
        <translation>支持版本：</translation>
    </message>
    <message>
        <source>Folder Size:</source>
        <translation>文件夹大小：</translation>
    </message>
    <message>
        <source>Path:</source>
        <translation>小路：</translation>
    </message>
    <message>
        <source>Steam URL:</source>
        <translation>蒸汽网址：</translation>
    </message>
    <message>
        <source>GitHub:</source>
        <translation>GitHub：</translation>
    </message>
    <message>
        <source>Version:</source>
        <translation>版本：</translation>
    </message>
    <message>
        <source>Last Touched:</source>
        <translation>最后一次接触：</translation>
    </message>
    <message>
        <source>Filesystem Modified:</source>
        <translation>文件系统修改：</translation>
    </message>
    <message>
        <source>Workshop Times:</source>
        <translation>工作坊时间：</translation>
    </message>
    <message>
        <source>Welcome to RimDex!</source>
        <translation>欢迎来到 RimDex！</translation>
    </message>
    <message>
        <source>Put your personal mod notes here!</source>
        <translation>将您的个人修改笔记放在这里！</translation>
    </message>
    <message>
        <source>(Update available)</source>
        <translation>（有更新）</translation>
    </message>
    <message>
        <source>None</source>
        <translation>没有任何</translation>
    </message>
</context>
<context>
    <name>ModListItemInner</name>
    <message>
        <source>Contains custom C# assemblies (custom code)</source>
        <translation>包含自定义 C# 程序集（自定义代码）</translation>
    </message>
    <message>
        <source>Contains custom content (textures / XML)</source>
        <translation>包含自定义内容（纹理 / XML）</translation>
    </message>
    <message>
        <source>Local mod that contains a git repository</source>
        <translation>包含 git 存储库的本地模组</translation>
    </message>
    <message>
        <source>Local mod that can be used with SteamCMD</source>
        <translation>可以与 SteamCMD 一起使用的本地模组</translation>
    </message>
    <message>
        <source>Recently updated on Workshop</source>
        <translation>最近更新了创意工坊</translation>
    </message>
    <message>
        <source>Official RimWorld content by Ludeon Studios</source>
        <translation>Ludeon Studios 官方的 RimWorld 内容</translation>
    </message>
    <message>
        <source>Installed locally</source>
        <translation>本地安装</translation>
    </message>
    <message>
        <source>Subscribed via Steam</source>
        <translation>通过 Steam 订阅</translation>
    </message>
    <message>
        <source>Translation available - This mod has a translation or is already localized</source>
        <translation>提供翻译 - 该模组有翻译或已经本地化</translation>
    </message>
    <message>
        <source>No translation found - This mod does not have a translation installed</source>
        <translation>未找到翻译 - 该模组未安装翻译</translation>
    </message>
    <message>
        <source>Not in latest save</source>
        <translation>不在最新存档中</translation>
    </message>
    <message>
        <source>In latest save</source>
        <translation>在最新存档中</translation>
    </message>
</context>
<context>
    <name>ModListWidget</name>
    <message>
        <source>Open folder</source>
        <translation>打开文件夹</translation>
    </message>
    <message>
        <source>Add new tags...</source>
        <translation>添加新标签...</translation>
    </message>
    <message>
        <source>Replace all tags...</source>
        <translation>替换所有标签...</translation>
    </message>
    <message>
        <source>Remove all tags</source>
        <translation>删除所有标签</translation>
    </message>
    <message>
        <source>Open URL in browser</source>
        <translation>在 浏览器 中打开模组页面</translation>
    </message>
    <message>
        <source>Copy URL to clipboard</source>
        <translation>复制 模组链接 到剪切板</translation>
    </message>
    <message>
        <source>Open mod in Steam</source>
        <translation>在 Steam 中打开模组界面</translation>
    </message>
    <message>
        <source>Convert local mod to SteamCMD</source>
        <translation>将本地模组转换为 Steamcmd 模组</translation>
    </message>
    <message>
        <source>Convert SteamCMD mod to local</source>
        <translation>将 Steam 模组转换为本地模组</translation>
    </message>
    <message>
        <source>Re-download mod with SteamCMD</source>
        <translation>使用 Steamcmd 重新下载</translation>
    </message>
    <message>
        <source>Update mod with git</source>
        <translation>使用 Git 更新模组</translation>
    </message>
    <message>
        <source>Convert Steam mod to local</source>
        <translation>将 Steam 模组转换为本地模组</translation>
    </message>
    <message>
        <source>Re-subscribe mod with Steam</source>
        <translation>重新订阅 Steam 模组</translation>
    </message>
    <message>
        <source>Unsubscribe mod with Steam</source>
        <translation>取消订阅 Steam 模组</translation>
    </message>
    <message>
        <source>Remove mod from SteamDB blacklist</source>
        <translation>将模组从 SteamDB 黑名单中移除</translation>
    </message>
    <message>
        <source>Add mod to SteamDB blacklist</source>
        <translation>将模组添加到 SteamDB 黑名单</translation>
    </message>
    <message>
        <source>Copy packageId to clipboard</source>
        <translation>复制 包名 到剪切板</translation>
    </message>
    <message>
        <source>Edit mod with Rule Editor</source>
        <translation>使用规则编辑器编辑模组</translation>
    </message>
    <message>
        <source>Toggle warning</source>
        <translation>启用/禁用警告</translation>
    </message>
    <message>
        <source>Find translations</source>
        <translation>查找翻译</translation>
    </message>
    <message>
        <source>Open folder(s)</source>
        <translation>打开文件夹</translation>
    </message>
    <message>
        <source>Open URL(s) in browser</source>
        <translation>在 浏览器 中打开模组</translation>
    </message>
    <message>
        <source>Convert local mod(s) to SteamCMD</source>
        <translation>将本地模组转换为 Steamcmd 模组</translation>
    </message>
    <message>
        <source>Convert SteamCMD mod(s) to local</source>
        <translation>将 SteamCMD 模组转换为本地模组</translation>
    </message>
    <message>
        <source>Re-download mod(s) with SteamCMD</source>
        <translation>使用 Steamcmd 重新下载模组</translation>
    </message>
    <message>
        <source>Update mod(s) with git</source>
        <translation>使用 Git 更新模组</translation>
    </message>
    <message>
        <source>Toggle warning(s)</source>
        <translation>启用/禁用警告</translation>
    </message>
    <message>
        <source>Convert Steam mod(s) to local</source>
        <translation>将 Steam 模组转换为本地模组</translation>
    </message>
    <message>
        <source>Re-subscribe mod(s) with Steam</source>
        <translation>重新订阅 Steam 模组</translation>
    </message>
    <message>
        <source>Unsubscribe mod(s) with Steam</source>
        <translation>取消订阅 Steam 模组</translation>
    </message>
    <message>
        <source>Tags</source>
        <translation>标签</translation>
    </message>
    <message>
        <source>Miscellaneous options</source>
        <translation>其他选项</translation>
    </message>
    <message>
        <source>Clipboard options</source>
        <translation>剪切板选项</translation>
    </message>
    <message>
        <source>Workshop mods options</source>
        <translation>创意工坊模组选项</translation>
    </message>
    <message>
        <source>Add divider here</source>
        <translation>在此添加分隔线</translation>
    </message>
    <message>
        <source>Add Divider</source>
        <translation>添加分隔线</translation>
    </message>
    <message>
        <source>Divider name:</source>
        <translation>分频器名称：</translation>
    </message>
    <message>
        <source>Are you sure?</source>
        <translation>你确定吗？</translation>
    </message>
    <message>
        <source>You have selected {len} git mods to be updated.</source>
        <translation>你选择了 {len} 个 git 模组进行更新。</translation>
    </message>
    <message>
        <source>Do you want to proceed?</source>
        <translation>你想要继续吗？</translation>
    </message>
    <message>
        <source>You have selected {len} mods for deletion + re-download.</source>
        <translation>你选择了 {len} 个模组进行删除和重新下载。</translation>
    </message>
    <message>
        <source>You have selected {len} mods for unsubscribe.</source>
        <translation>你选择了 {len} 个模组进行取消订阅。</translation>
    </message>
    <message>
        <source>Database not available</source>
        <translation>数据库不可用</translation>
    </message>
    <message>
        <source>Steam Workshop metadata database is not loaded. Please build the database first using the Database Builder.</source>
        <translation>Steam 创意工坊元数据数据库未加载。请首先使用数据库生成器构建数据库。</translation>
    </message>
    <message>
        <source>No translations found</source>
        <translation>没有找到翻译</translation>
    </message>
    <message>
        <source>No translation mods were found for this mod in the Steam Workshop database.</source>
        <translation>在 Steam 创意工坊数据库中未找到此模组的翻译模组。</translation>
    </message>
    <message>
        <source>Select Translation</source>
        <translation>选择翻译</translation>
    </message>
    <message>
        <source>Found {len(translation_mods)} translation(s). Select one to open:</source>
        <translation>找到 {len(translation_mods)} 翻译。选择一项打开：</translation>
    </message>
    <message>
        <source>Open</source>
        <translation>打开</translation>
    </message>
    <message>
        <source>Cancel</source>
        <translation>取消</translation>
    </message>
    <message>
        <source>&lt;br&gt;This operation will recursively delete all mod files, except for .dds textures found, and attempt to re-download the mods via SteamCMD. Do you want to proceed?</source>
        <translation>&lt;br&gt;此操作将递归删除所有 mod 文件（找到的 .dds 纹理除外），并尝试通过 SteamCMD 重新下载 mod。您想继续吗？</translation>
    </message>
    <message>
        <source>You have selected {len} mods for resubscribe:(unsubscribe + subscribe).</source>
        <translation>您已选择 {len} 个 mod 进行重新订阅：（取消订阅 + 订阅）。</translation>
    </message>
    <message>
        <source>Add comment</source>
        <translation>添加备注</translation>
    </message>
    <message>
        <source>Enter a comment providing your reasoning for wanting to blacklist this mod: </source>
        <translation>输入你的备注，提供你添加此模组到黑名单的原因：</translation>
    </message>
    <message>
        <source>Unable to add to blacklist</source>
        <translation>无法添加到黑名单</translation>
    </message>
    <message>
        <source>Comment was not provided or entry was cancelled. Comments are REQUIRED for this action!</source>
        <translation>未提供备注或条目已取消。此操作必须提供备注！</translation>
    </message>
    <message>
        <source>This will remove the selected mod, </source>
        <translation>这将会移除所有选择的模组</translation>
    </message>
    <message>
        <source>Replace tags</source>
        <translation>替换标签</translation>
    </message>
    <message>
        <source>Add tags</source>
        <translation>添加标签</translation>
    </message>
    <message>
        <source>Rename divider</source>
        <translation>重命名分隔线</translation>
    </message>
    <message>
        <source>Expand</source>
        <translation>扩张</translation>
    </message>
    <message>
        <source>Collapse</source>
        <translation>坍塌</translation>
    </message>
    <message>
        <source>Delete divider</source>
        <translation>删除分隔线</translation>
    </message>
    <message>
        <source>Rename Divider</source>
        <translation>重命名分隔线</translation>
    </message>
    <message>
        <source>New name:</source>
        <translation>新名称：</translation>
    </message>
    <message>
        <source>
Missing Dependencies:</source>
        <translation>
缺少依赖：</translation>
    </message>
    <message>
        <source>
Incompatibilities:</source>
        <translation>
不兼容：</translation>
    </message>
    <message>
        <source>
Incompatible (per other mod&apos;s rules):</source>
        <translation>不兼容（根据其他模组的规则）：</translation>
    </message>
    <message>
        <source>
Should be Loaded After:</source>
        <translation>
应在以下模组之后加载：</translation>
    </message>
    <message>
        <source>
Should be Loaded Before:</source>
        <translation>
应在以下模组之前加载：</translation>
    </message>
    <message>
        <source>
Mod and Game Version Mismatch</source>
        <translation>
模组和游戏版本不匹配</translation>
    </message>
    <message>
        <source>
An alternative updated mod is recommended:
{alternative}</source>
        <translation>
推荐一个替代的更新模组：
{alternative}</translation>
    </message>
    <message>
        <source>Change mod color</source>
        <translation>更改模组颜色</translation>
    </message>
    <message>
        <source>Reset mod color</source>
        <translation>重置模组颜色</translation>
    </message>
    <message>
        <source>&lt;br&gt;This operation will potentially delete .dds textures leftover. Steam is unreliable for this. Do you want to proceed?</source>
        <translation>&lt;br&gt;此操作可能会删除剩余的 .dds 纹理。 Steam对此并不可靠。您想继续吗？</translation>
    </message>
    <message>
        <source>&lt;br&gt;Do you want to proceed?</source>
        <translation>&lt;br&gt;您想继续吗？</translation>
    </message>
    <message>
        <source>
Alternative Dependencies:</source>
        <translation>替代依赖：</translation>
    </message>
    <message>
        <source>Open folder in text editor</source>
        <translation>在文本编辑器中打开文件夹</translation>
    </message>
    <message>
        <source>Open folder(s) in text editor</source>
        <translation>在文本编辑器中打开文件夹</translation>
    </message>
</context>
<context>
    <name>ModsPanel</name>
    <message>
        <source>Hide Filter Disabled</source>
        <translation>隐藏过滤器已禁用</translation>
    </message>
    <message>
        <source>Active [0]</source>
        <translation>启用 [0]</translation>
    </message>
    <message>
        <source>Tags</source>
        <translation>标签</translation>
    </message>
    <message>
        <source>Colors</source>
        <translation>颜色</translation>
    </message>
    <message>
        <source>0 updated</source>
        <translation>0 更新</translation>
    </message>
    <message>
        <source>Click to only show mods recently updated on the Workshop</source>
        <translation>单击以仅显示创意工坊中最近更新的模组</translation>
    </message>
    <message>
        <source>Workshop Updated</source>
        <translation>研讨会已更新</translation>
    </message>
    <message>
        <source>{padding}{count} updated</source>
        <translation>{padding}{count} 已更新</translation>
    </message>
    <message>
        <source>Database not available</source>
        <translation>数据库不可用</translation>
    </message>
    <message>
        <source>Steam Workshop metadata database is not loaded. Please build the database first using the Database Builder.</source>
        <translation>Steam 创意工坊元数据数据库未加载。请首先使用数据库生成器构建数据库。</translation>
    </message>
    <message>
        <source>No Translations Found</source>
        <translation>未找到翻译</translation>
    </message>
    <message>
        <source>No applicable translation mods were found for your active mod list.</source>
        <translation>未找到适用于您的活动模组列表的翻译模组。</translation>
    </message>
    <message>
        <source>Translations Added</source>
        <translation>添加翻译</translation>
    </message>
    <message>
        <source>Successfully added {count} translation mods to the active list.</source>
        <translation>已成功将 {count} 个翻译模组添加到活动列表中。</translation>
    </message>
    <message>
        <source>No New Translations</source>
        <translation>没有新翻译</translation>
    </message>
    <message>
        <source>All found translation mods are already active.</source>
        <translation>所有找到的翻译模块都已处于活动状态。</translation>
    </message>
    <message>
        <source>Hide Filter Enabled</source>
        <translation>隐藏过滤器已启用</translation>
    </message>
    <message>
        <source>Inactive [0]</source>
        <translation>未启用 [0]</translation>
    </message>
    <message>
        <source>Search by...</source>
        <translation>按...搜索</translation>
    </message>
    <message>
        <source>Name</source>
        <translation>名称</translation>
    </message>
    <message>
        <source>PackageId</source>
        <translation>包名</translation>
    </message>
    <message>
        <source>Color</source>
        <translation>颜色</translation>
    </message>
    <message>
        <source>Notes</source>
        <translation>笔记</translation>
    </message>
    <message>
        <source>Author(s)</source>
        <translation>作者</translation>
    </message>
    <message>
        <source>PublishedFileId</source>
        <translation>发布文件 ID</translation>
    </message>
    <message>
        <source>0 warnings</source>
        <translation>0 警告</translation>
    </message>
    <message>
        <source>Click to only show mods with warnings</source>
        <translation>点击仅显示有警告的模组</translation>
    </message>
    <message>
        <source>Click to only show mods with errors</source>
        <translation>点击仅显示有错误的模组</translation>
    </message>
    <message>
        <source>Check &quot;Use This Instead&quot; Database</source>
        <translation>查看&quot;替代为此&quot;数据库</translation>
    </message>
    <message>
        <source>Check Dependencies</source>
        <translation>查看依赖</translation>
    </message>
    <message>
        <source>Active</source>
        <translation>启用</translation>
    </message>
    <message>
        <source>Inactive</source>
        <translation>未启用</translation>
    </message>
    <message>
        <source>Version</source>
        <translation>版本</translation>
    </message>
    <message>
        <source>Sort inactive mods by</source>
        <translation>按以下方式排序未启用的模组</translation>
    </message>
    <message>
        <source>Author</source>
        <translation>作者</translation>
    </message>
    <message>
        <source>Modified Time</source>
        <translation>修改时间</translation>
    </message>
    <message>
        <source>Folder Size</source>
        <translation>文件夹大小</translation>
    </message>
    <message>
        <source>Toggle sort order</source>
        <translation>切换排序顺序</translation>
    </message>
    <message>
        <source>Desc</source>
        <translation>降序</translation>
    </message>
    <message>
        <source>Asc</source>
        <translation>升序</translation>
    </message>
    <message>
        <source>Calculating folder sizes...</source>
        <translation>正在计算文件夹大小...</translation>
    </message>
    <message>
        <source>0 new</source>
        <translation>0 新</translation>
    </message>
    <message>
        <source>Click to only show active mods not in latest save</source>
        <translation>点击仅显示未在最新存档中的活动模组</translation>
    </message>
    <message>
        <source>{padding}{num} warning(s)</source>
        <translation>{padding}{num} 个警告</translation>
    </message>
    <message>
        <source>{padding}{num} error(s)</source>
        <translation>{padding}{num} 个错误</translation>
    </message>
    <message>
        <source>{padding}{count} new</source>
        <translation>{padding}{count} 新</translation>
    </message>
</context>
<context>
    <name>ModsPanelController</name>
    <message>
        <source>Confirm Resetting Warning Toggles</source>
        <translation>确认重置警告开关</translation>
    </message>
    <message>
        <source>Are you sure you want to reset all warning/error toggles?</source>
        <translation>您确定要重置所有警告/错误切换吗？</translation>
    </message>
    <message>
        <source>Reset All</source>
        <translation>全部重置</translation>
    </message>
    <message>
        <source>Cancel</source>
        <translation>取消</translation>
    </message>
    <message>
        <source>Confirm Resetting Mod Colors</source>
        <translation>确认重置 Mod 颜色</translation>
    </message>
    <message>
        <source>Are you sure you want to reset all mod colors?</source>
        <translation>您确定要重置所有模组颜色吗？</translation>
    </message>
</context>
<context>
    <name>PlayerLogTab</name>
    <message>
        <source>File Info</source>
        <translation>文件信息</translation>
    </message>
    <message>
        <source>Path:</source>
        <translation>路径：</translation>
    </message>
    <message>
        <source>Size:</source>
        <translation>大小：</translation>
    </message>
    <message>
        <source>Modified:</source>
        <translation>修改时间：</translation>
    </message>
    <message>
        <source>Statistics</source>
        <translation>统计信息</translation>
    </message>
    <message>
        <source>Loading file... %p%</source>
        <translation>正在加载文件...%p%</translation>
    </message>
    <message>
        <source>Total Lines: {total_lines}</source>
        <translation>总行数: {total_lines}</translation>
    </message>
    <message>
        <source>Infos: {infos}</source>
        <translation>信息: {infos}</translation>
    </message>
    <message>
        <source>Keybinds: {keybinds}</source>
        <translation>按键绑定: {keybinds}</translation>
    </message>
    <message>
        <source>Mod Issues: {mod_issues}</source>
        <translation>模组问题: {mod_issues}</translation>
    </message>
    <message>
        <source>Warnings: {warnings}</source>
        <translation>警告: {warnings}</translation>
    </message>
    <message>
        <source>Errors: {errors}</source>
        <translation>错误: {errors}</translation>
    </message>
    <message>
        <source>Exceptions: {exceptions}</source>
        <translation>异常: {exceptions}</translation>
    </message>
    <message>
        <source>All Issues: {all_issues}</source>
        <translation>所有问题: {all_issues}</translation>
    </message>
    <message>
        <source>Auto Load Game Log on Startup</source>
        <translation>启动时自动加载游戏日志</translation>
    </message>
    <message>
        <source>If checked, the Game log will be loaded automatically on startup.</source>
        <translation>如果选中，游戏日志将在启动时自动加载。</translation>
    </message>
    <message>
        <source>Enable Real-Time Log Monitoring</source>
        <translation>启用实时日志监控</translation>
    </message>
    <message>
        <source>Enable real-time monitoring of Player.log file changes.</source>
        <translation>启用对 Player.log 文件更改的实时监控。</translation>
    </message>
    <message>
        <source>Refresh</source>
        <translation>刷新</translation>
    </message>
    <message>
        <source>Export</source>
        <translation>导出</translation>
    </message>
    <message>
        <source>Clear Log Display</source>
        <translation>清除日志显示</translation>
    </message>
    <message>
        <source>Load Game Log</source>
        <translation>加载游戏日志</translation>
    </message>
    <message>
        <source>Loads the game&apos;s Player.log file.</source>
        <translation>加载游戏的 Player.log 文件。</translation>
    </message>
    <message>
        <source>Load Log from File</source>
        <translation>从文件加载日志</translation>
    </message>
    <message>
        <source>Open a file dialog to select a log file</source>
        <translation>打开文件对话框以选择日志文件</translation>
    </message>
    <message>
        <source>Load Log from Link</source>
        <translation>从链接加载日志</translation>
    </message>
    <message>
        <source>Load log content from a URL</source>
        <translation>从 URL 加载日志内容</translation>
    </message>
    <message>
        <source>Search and Filter</source>
        <translation>搜索和过滤</translation>
    </message>
    <message>
        <source>Search log entries...</source>
        <translation>搜索日志条目...</translation>
    </message>
    <message>
        <source>All Entries</source>
        <translation>所有条目</translation>
    </message>
    <message>
        <source>Infos Only</source>
        <translation>仅信息</translation>
    </message>
    <message>
        <source>Keybinds Only</source>
        <translation>仅按键绑定</translation>
    </message>
    <message>
        <source>Mod Issues</source>
        <translation>模组问题</translation>
    </message>
    <message>
        <source>Warnings Only</source>
        <translation>仅警告</translation>
    </message>
    <message>
        <source>Errors Only</source>
        <translation>仅错误</translation>
    </message>
    <message>
        <source>Exceptions Only</source>
        <translation>仅异常</translation>
    </message>
    <message>
        <source>All Issues</source>
        <translation>所有问题</translation>
    </message>
    <message>
        <source>Filter by mod name...</source>
        <translation>按模组名称过滤...</translation>
    </message>
    <message>
        <source>Highlight Color</source>
        <translation>高亮颜色</translation>
    </message>
    <message>
        <source>Pick color for search and navigation highlighting</source>
        <translation>选择搜索和导航高亮的颜色</translation>
    </message>
    <message>
        <source>Previous</source>
        <translation>上一个</translation>
    </message>
    <message>
        <source>Next</source>
        <translation>下一个</translation>
    </message>
    <message>
        <source>Quick Navigation</source>
        <translation>快速导航</translation>
    </message>
    <message>
        <source>Scroll to End</source>
        <translation>滚动到末尾</translation>
    </message>
    <message>
        <source>Scroll to the end of the log display</source>
        <translation>滚动到日志显示的末尾</translation>
    </message>
    <message>
        <source>Reading file... %p%</source>
        <translation>正在读取文件...%p%</translation>
    </message>
    <message>
        <source>Path: Loaded from URL: {url}</source>
        <translation>路径: 从 URL 加载: {url}</translation>
    </message>
    <message>
        <source>Path: Loaded from URL</source>
        <translation>路径: 从 URL 加载</translation>
    </message>
    <message>
        <source>Size: {size:,} bytes</source>
        <translation>大小: {size:,} 字节</translation>
    </message>
    <message>
        <source>Modified: N/A</source>
        <translation>修改时间: 不适用</translation>
    </message>
    <message>
        <source>Path: N/A</source>
        <translation>路径: 不适用</translation>
    </message>
    <message>
        <source>Size: N/A</source>
        <translation>大小: 不适用</translation>
    </message>
    <message>
        <source>Player log file not found.</source>
        <translation>未找到玩家日志文件。</translation>
    </message>
    <message>
        <source>Reading log from URL... %p%</source>
        <translation>从 URL 读取日志...%p%</translation>
    </message>
    <message>
        <source>Enter URL:</source>
        <translation>输入 URL：</translation>
    </message>
    <message>
        <source>Log loaded successfully from URL</source>
        <translation>日志已成功从 URL 加载</translation>
    </message>
    <message>
        <source>Failed to load log from URL</source>
        <translation>从 URL 加载日志失败</translation>
    </message>
    <message>
        <source>Failed due to error: {error}</source>
        <translation>失败，错误信息: {error}</translation>
    </message>
    <message>
        <source>Path: {path_str}</source>
        <translation>路径: {path_str}</translation>
    </message>
    <message>
        <source>Size: {size_str}</source>
        <translation>大小: {size_str}</translation>
    </message>
    <message>
        <source>Modified: {modified_str}</source>
        <translation>修改时间: {modified_str}</translation>
    </message>
    <message>
        <source>Info</source>
        <translation>信息</translation>
    </message>
    <message>
        <source>Keybind</source>
        <translation>按键绑定</translation>
    </message>
    <message>
        <source>Mod_issue</source>
        <translation>模组问题</translation>
    </message>
    <message>
        <source>Warning</source>
        <translation>警告</translation>
    </message>
    <message>
        <source>Error</source>
        <translation>错误</translation>
    </message>
    <message>
        <source>Exception</source>
        <translation>异常</translation>
    </message>
    <message>
        <source>Jump to previous {lower} entry</source>
        <translation>跳转到上一个 {lower} 条目</translation>
    </message>
    <message>
        <source>Jump to next {lower} entry</source>
        <translation>跳转到下一个 {lower} 条目</translation>
    </message>
    <message>
        <source>Total Lines: 0</source>
        <translation>总行数: 0</translation>
    </message>
    <message>
        <source>Infos: 0</source>
        <translation>信息: 0</translation>
    </message>
    <message>
        <source>Keybinds: 0</source>
        <translation>按键绑定: 0</translation>
    </message>
    <message>
        <source>Mod Issues: 0</source>
        <translation>模组问题: 0</translation>
    </message>
    <message>
        <source>Warnings: 0</source>
        <translation>警告: 0</translation>
    </message>
    <message>
        <source>Errors: 0</source>
        <translation>错误: 0</translation>
    </message>
    <message>
        <source>Exceptions: 0</source>
        <translation>异常: 0</translation>
    </message>
    <message>
        <source>All Issues: 0</source>
        <translation>所有问题: 0</translation>
    </message>
    <message>
        <source>Controls</source>
        <translation>控制</translation>
    </message>
    <message>
        <source>Pick Highlight Color</source>
        <translation>选择高亮颜色</translation>
    </message>
</context>
<context>
    <name>Rentry Auth Code Not Found </name>
    <message>
        <source>RimDex can work without rentry auth code. But To enable full functionality of renry.co you need to email support@rentry.co and request an auth code. Then paste it into Settings -&gt; Advanced -&gt; Rentry Auth.</source>
        <translation>RimDex 可以在没有 rentry 授权码的情况下工作。但要启用 rentry.co 的全部功能，你需要发送邮件到 support@rentry.co 并请求一个授权码。然后将其粘贴到 设置 -&gt; 高级 -&gt; Rentry 授权。</translation>
    </message>
</context>
<context>
    <name>RentryError</name>
    <message>
        <source>Failed to fetch Rentry Content</source>
        <translation>无法获取 Rentry 内容</translation>
    </message>
    <message>
        <source>Rentry returned status code: {code}</source>
        <translation>Rentry 返回状态码: {code}</translation>
    </message>
    <message>
        <source>RimDex failed to fetch the content from the provided Rentry link. This may be due to an invalid link, your internet connection, or Rentry.co being down. It may also be the result of a captcha. Please try again later.</source>
        <translation>RimDex 无法从提供的 Rentry 链接获取内容。这可能是由于无效的链接、你的互联网连接或 Rentry.co 宕机。也可能是验证码的结果。请稍后再试。</translation>
    </message>
    <message>
        <source>Network Error</source>
        <translation>网络错误</translation>
    </message>
    <message>
        <source>Network error occurred while processing Rentry, Please check your internet connection.</source>
        <translation>在处理 Rentry 时发生网络错误，请检查你的互联网连接。</translation>
    </message>
    <message>
        <source>Rentry Auth Code Not Found</source>
        <translation>Rentry 授权码未找到</translation>
    </message>
</context>
<context>
    <name>RentryImport</name>
    <message>
        <source>Enter Rentry.co link</source>
        <translation>输入 Rentry.co 链接</translation>
    </message>
    <message>
        <source>Enter the Rentry.co link:</source>
        <translation>输入 Rentry.co 链接：</translation>
    </message>
    <message>
        <source>Invalid Rentry Link</source>
        <translation>无效的 Rentry 链接</translation>
    </message>
    <message>
        <source>Invalid Rentry link, Please enter a valid Rentry link.</source>
        <translation>无效的 Rentry 链接，请输入一个有效的 Rentry 链接。</translation>
    </message>
    <message>
        <source>Error</source>
        <translation>错误</translation>
    </message>
    <message>
        <source>An error occurred: {e}</source>
        <translation>发生错误: {e}</translation>
    </message>
</context>
<context>
    <name>RentryUpload</name>
    <message>
        <source>Error</source>
        <translation>错误</translation>
    </message>
    <message>
        <source>An error occurred: {e}</source>
        <translation>发生错误: {e}</translation>
    </message>
</context>
<context>
    <name>RuleEditor</name>
    <message>
        <source>No mod currently being edited</source>
        <translation>当前没有正在编辑的模组</translation>
    </message>
    <message>
        <source>About.xml (loadAfter)</source>
        <translation>About.xml (loadAfter)</translation>
    </message>
    <message>
        <source>About.xml (loadBefore)</source>
        <translation>About.xml (loadBefore)</translation>
    </message>
    <message>
        <source>Community Rules (loadAfter)</source>
        <translation>社区规则 (loadAfter)</translation>
    </message>
    <message>
        <source>Community Rules (loadBefore)</source>
        <translation>社区规则 (loadBefore)</translation>
    </message>
    <message>
        <source>Force load at bottom of list</source>
        <translation>在列表底部加载</translation>
    </message>
    <message>
        <source>User Rules (loadAfter)</source>
        <translation>用户规则 (loadAfter)</translation>
    </message>
    <message>
        <source>User Rules (loadBefore)</source>
        <translation>用户规则 (loadBefore)</translation>
    </message>
    <message>
        <source>Name</source>
        <translation>名称</translation>
    </message>
    <message>
        <source>PackageId</source>
        <translation>包名</translation>
    </message>
    <message>
        <source>Rule source</source>
        <translation>规则来源</translation>
    </message>
    <message>
        <source>Rule type</source>
        <translation>规则类型</translation>
    </message>
    <message>
        <source>Comment</source>
        <translation>备注</translation>
    </message>
    <message>
        <source>Save rules to communityRules.json</source>
        <translation>保存规则到 communityRules.json</translation>
    </message>
    <message>
        <source>Save rules to userRules.json</source>
        <translation>保存规则到 userRules.json</translation>
    </message>
    <message>
        <source>Search mods by name</source>
        <translation>按名称搜索模组</translation>
    </message>
    <message>
        <source>Duplicate rule</source>
        <translation>重复规则</translation>
    </message>
    <message>
        <source>Tried to add duplicate rule.</source>
        <translation>尝试添加重复的规则</translation>
    </message>
    <message>
        <source>Skipping creation of duplicate rule!</source>
        <translation>跳过创建重复的规则！</translation>
    </message>
    <message>
        <source>Enter comment</source>
        <translation>输入备注</translation>
    </message>
    <message>
        <source>Enter a comment to annotate why this rule exists.
                      This is useful for your own records, as well as others.</source>
        <translation>输入备注，提供你添加此规则的原因：
                      这对你自己的记录以及其他人都有用。</translation>
    </message>
    <message>
        <source>Rules from mods&apos;s About.xml cannot be modified. Only &apos;Community Rules&apos; and &apos;User Rules&apos; are allowed.</source>
        <translation>从模组 About.xml 的规则不能被修改。只有 &apos;Community Rules&apos; 和 &apos;User Rules&apos; 是被允许的。</translation>
    </message>
    <message>
        <source>Rules can be Modified.</source>
        <translation>规则可以被修改。</translation>
    </message>
    <message>
        <source>Editing rules for: {name}</source>
        <translation>正在编辑规则：{name}</translation>
    </message>
    <message>
        <source>Show About.xml rules</source>
        <translation>显示 About.xml 规则</translation>
    </message>
    <message>
        <source>Edit Community Rules</source>
        <translation>编辑社区规则</translation>
    </message>
    <message>
        <source>Edit User Rules</source>
        <translation>编辑用户规则</translation>
    </message>
    <message>
        <source>Hide About.xml rules</source>
        <translation>隐藏 About.xml 规则</translation>
    </message>
    <message>
        <source>Lock Community Rules</source>
        <translation>隐藏社区规则</translation>
    </message>
    <message>
        <source>Lock User Rules</source>
        <translation>隐藏用户规则</translation>
    </message>
    <message>
        <source>Enter a comment to annotate why this rule exists.This is useful for your own records, as well as others.</source>
        <translation>输入备注，提供你添加此规则的原因：这对你自己的记录以及其他人都有用。</translation>
    </message>
    <message>
        <source>Enter a comment to annotate why this rule exists. This is useful for your own records, as well as others.</source>
        <translation>输入备注，提供你添加此规则的原因：这对你自己的记录以及其他人都有用。</translation>
    </message>
    <message>
        <source>Open this mod in the editor</source>
        <translation>在规则编辑器中打开模组</translation>
    </message>
    <message>
        <source>Remove this rule</source>
        <translation>删除此规则</translation>
    </message>
    <message>
        <source>About.xml (incompatibilitiesWith)</source>
        <translation>About.xml (incompatibilitiesWith)</translation>
    </message>
    <message>
        <source>Community Rules (incompatibilitiesWith)</source>
        <translation>社区规则 (incompatibilitiesWith)</translation>
    </message>
    <message>
        <source>User Rules (incompatibilitiesWith)</source>
        <translation>用户规则 (incompatibilitiesWith)</translation>
    </message>
    <message>
        <source>Force load at top of list</source>
        <translation>在列表顶部加载</translation>
    </message>
</context>
<context>
    <name>RunnerPanel</name>
    <message>
        <source>Clear the text currently displayed by the runner</source>
        <translation>清除运行程序中当前显示的文本</translation>
    </message>
    <message>
        <source>Re-run the process last used by the runner</source>
        <translation>重新运行上次由运行器使用的进程</translation>
    </message>
    <message>
        <source>Kill a process currently being executed by the runner</source>
        <translation>关闭当前由运行器执行的进程</translation>
    </message>
    <message>
        <source>SteamCMD downloader</source>
        <translation>SteamCMD 下载器</translation>
    </message>
    <message>
        <source>Process Complete</source>
        <translation>处理完成</translation>
    </message>
    <message>
        <source>Process complete, you can close the window.</source>
        <translation>处理完成，你可以关闭窗口。</translation>
    </message>
    <message>
        <source>Close Window</source>
        <translation>关闭窗口</translation>
    </message>
    <message>
        <source>Ok</source>
        <translation>确定</translation>
    </message>
    <message>
        <source>Save the current output to a file</source>
        <translation>将当前输出保存到文件</translation>
    </message>
    <message>
        <source>Save Runner Output</source>
        <translation>保存运行器输出</translation>
    </message>
    <message>
        <source>Text files (*.txt)</source>
        <translation>文本文件 (*.txt)</translation>
    </message>
    <message>
        <source>SteamCMD Downloader Login error</source>
        <translation>SteamCMD 下载器登录错误</translation>
    </message>
    <message>
        <source>SteamCMD reported a login error. Please ensure you are connected to internet and steamcmd is not blocked by your firewall.</source>
        <translation>SteamCMD 报告了登录误差。请确保你连接到网络，并且防火墙不会阻止 SteamCMD。</translation>
    </message>
    <message>
        <source>SteamCMD failed to download mod(s)! Would you like to retry download of the mods that failed?&lt;br&gt;&lt;br&gt;Click &apos;Show Details&apos; to see a list of mods that failed.</source>
        <translation>SteamCMD 无法下载模组！您想重试下载失败的模组吗？&lt;br&gt;&lt;br&gt;单击“显示详细信息”可查看失败的模组列表。</translation>
    </message>
</context>
<context>
    <name>SearchWorker</name>
    <message>
        <source>Searching in: {root_path}</source>
        <translation>正在搜索：{root_path}</translation>
    </message>
    <message>
        <source>Search complete</source>
        <translation>搜索完成</translation>
    </message>
</context>
<context>
    <name>Settings</name>
    <message>
        <source>Settings Load Error</source>
        <translation>设置加载错误</translation>
    </message>
    <message>
        <source>Your settings file seems to be corrupted and cannot be loaded. RimDex found a backup at {}. Do you want to attempt to recover your settings from this backup?</source>
        <translation>您的设置文件似乎已损坏且无法加载。 RimDex 在 {} 找到了备份。您想尝试从此备份恢复您的设置吗？</translation>
    </message>
    <message>
        <source>Your settings file seems to be corrupted and cannot be loaded. RimDex found an old backup at {}. Do you want to attempt to recover your settings from this backup?</source>
        <translation>您的设置文件似乎已损坏且无法加载。 RimDex 在 {} 找到了旧备份。您想尝试从此备份恢复您的设置吗？</translation>
    </message>
    <message>
        <source>Your settings file seems to be corrupted and cannot be loaded. No backup file was found, RimDex will reset your settings to defaults.</source>
        <translation>您的设置文件似乎已损坏且无法加载。未找到备份文件，RimDex 会将您的设置重置为默认值。</translation>
    </message>
    <message>
        <source>If you proceed, a backup of the corrupted file will be saved to {}.</source>
        <translation>如果继续，损坏文件的备份将保存到 {}。</translation>
    </message>
    <message>
        <source>Proceed</source>
        <translation>继续</translation>
    </message>
    <message>
        <source>Exit RimDex</source>
        <translation>退出边缘排序</translation>
    </message>
    <message>
        <source>Settings Recovery Failed</source>
        <translation>设置恢复失败</translation>
    </message>
    <message>
        <source>RimDex failed to recover your settings from the backup. You may be able to manually recover your settings by restoring &quot;settings.json.backup&quot; or &quot;settings.json.backup.old&quot; from {} to {}.</source>
        <translation>RimDex 无法从备份恢复您的设置。您可以通过将“settings.json.backup”或“settings.json.backup.old”从 {} 恢复到 {} 来手动恢复您的设置。</translation>
    </message>
</context>
<context>
    <name>SettingsController</name>
    <message>
        <source>Steam Integration</source>
        <translation>蒸汽集成</translation>
    </message>
    <message>
        <source>Reset to defaults</source>
        <translation>恢复默认设置</translation>
    </message>
    <message>
        <source>Are you sure you want to reset all settings to their default values?</source>
        <translation>你确定要将所有设置恢复为默认值吗？</translation>
    </message>
    <message>
        <source>The selected game folder does not contain a valid RimWorld executable.&lt;br&gt;&lt;br&gt;Please select a valid game location.&lt;br&gt;&lt;br&gt;Windows: RimWorldWin64.exe or RimWorldWin.exe&lt;br&gt;&lt;br&gt;Mac: RimworldMac.app&lt;br&gt;&lt;br&gt;Linux: RimWorldLinux&lt;br&gt;&lt;br&gt;RimWorldWin64.exe or RimWorldWin.exe if you using windows version of the game on Linux</source>
        <translation>所选游戏文件夹不包含有效的 RimWorld 可执行文件。&lt;br&gt;&lt;br&gt;请选择有效的游戏位置。&lt;br&gt;&lt;br&gt;Windows：RimWorldWin64.exe 或 RimWorldWin.exe&lt;br&gt;&lt;br&gt;Mac：RimworldMac.app&lt;br&gt;&lt;br&gt;Linux：RimWorldLinux&lt;br&gt;&lt;br&gt;RimWorldWin64.exe 或 RimWorldWin.exe（如果您在 Linux 上使用 Windows 版本的游戏）</translation>
    </message>
    <message>
        <source>The selected config folder does not contain ModsConfig.xml.&lt;br&gt;&lt;br&gt;Please select a valid config folder.&lt;br&gt;&lt;br&gt;If you have not launched the game before,&lt;br&gt;&lt;br&gt;Please launch the game at least once to generate the necessary config files.</source>
        <translation>所选的配置文件夹不包含 ModsConfig.xml。&lt;br&gt;&lt;br&gt;请选择有效的配置文件夹。&lt;br&gt;&lt;br&gt;如果您之前未启动过游戏，&lt;br&gt;&lt;br&gt;请至少启动游戏一次以生成必要的配置文件。</translation>
    </message>
    <message>
        <source>The selected local mods folder location is not a valid directory.&lt;br&gt;&lt;br&gt;Please select a valid folder for local mods.&lt;br&gt;&lt;br&gt;The local mods folder should be a &apos;Mods&apos; subfolder within the game folder.</source>
        <translation>所选的本地 mods 文件夹位置不是有效的目录。&lt;br&gt;&lt;br&gt;请为本地 mods 选择一个有效的文件夹。&lt;br&gt;&lt;br&gt;本地 mods 文件夹应该是游戏文件夹内的“Mods”子文件夹。</translation>
    </message>
    <message>
        <source>Invalid Game Location</source>
        <translation>无效的游戏路径</translation>
    </message>
    <message>
        <source>Invalid Local Mods Folder</source>
        <translation>无效的本地 Mod 文件夹</translation>
    </message>
    <message>
        <source>Invalid Config Folder</source>
        <translation>无效的配置文件夹</translation>
    </message>
</context>
<context>
    <name>SettingsDialog</name>
    <message>
        <source>Settings</source>
        <translation>设置</translation>
    </message>
    <message>
        <source>Reset to Defaults</source>
        <translation>恢复默认设置</translation>
    </message>
    <message>
        <source>Cancel</source>
        <translation>取消</translation>
    </message>
    <message>
        <source>OK</source>
        <translation>确认</translation>
    </message>
    <message>
        <source>Locations</source>
        <translation>路径</translation>
    </message>
    <message>
        <source>Clear All Locations</source>
        <translation>清空所有路径</translation>
    </message>
    <message>
        <source>Autodetect</source>
        <translation>自动检测</translation>
    </message>
    <message>
        <source>Open…</source>
        <translation>打开</translation>
    </message>
    <message>
        <source>Choose…</source>
        <translation>选择</translation>
    </message>
    <message>
        <source>Clear…</source>
        <translation>清空</translation>
    </message>
    <message>
        <source>Use Default</source>
        <translation>使用默认</translation>
    </message>
    <message>
        <source>Leave empty to use default location</source>
        <translation>留空则使用默认位置</translation>
    </message>
    <message>
        <source>Game Launch</source>
        <translation>游戏启动</translation>
    </message>
    <message>
        <source>Databases</source>
        <translation>数据库</translation>
    </message>
    <message>
        <source>Automatically backup saves on first daily launch</source>
        <translation>每日首次启动游戏时自动备份存档</translation>
    </message>
    <message>
        <source>If enabled, RimDex will automatically backup saves on the first daily launch.</source>
        <translation>如果启用，RimDex将在每日首次启动游戏时自动备份存档。</translation>
    </message>
    <message>
        <source>Number of backups to keep:</source>
        <translation>保留备份数量：</translation>
    </message>
    <message>
        <source>The number of backups to keep. Set to -1 to keep all backups, 0 to delete all.</source>
        <translation>保留的备份数量。设置为-1保留所有备份，设置为0删除所有备份。</translation>
    </message>
    <message>
        <source>Number of saves to compress:</source>
        <translation>压缩的存档数量：</translation>
    </message>
    <message>
        <source>The number of recent saves to include in the backup. Set to -1 to compress all saves, 0 to compress none.</source>
        <translation>要包含在备份中的最近存档数量。设置为-1表示压缩所有存档，设置为0表示不压缩任何存档。</translation>
    </message>
    <message>
        <source>None</source>
        <translation>无</translation>
    </message>
    <message>
        <source>No {none_lbl} will be used.</source>
        <translation>不使用 {none_lbl}</translation>
    </message>
    <message>
        <source>GitHub</source>
        <translation>GitHub</translation>
    </message>
    <message>
        <source>Upload…</source>
        <translation>上传</translation>
    </message>
    <message>
        <source>Download…</source>
        <translation>下载</translation>
    </message>
    <message>
        <source>URL</source>
        <translation>网址</translation>
    </message>
    <message>
        <source>https://github.com/.../archive/refs/heads/main.zip</source>
        <translation>https://github.com/.../archive/refs/heads/main.zip</translation>
    </message>
    <message>
        <source>Local File</source>
        <translation>本地文件</translation>
    </message>
    <message>
        <source>Community Rules database</source>
        <translation>社区规则数据库</translation>
    </message>
    <message>
        <source>community rules database</source>
        <translation>社区规则数据库</translation>
    </message>
    <message>
        <source>Steam Workshop database</source>
        <translation>Steam 创意工坊数据库</translation>
    </message>
    <message>
        <source>&quot;No Version Warning&quot; Database</source>
        <translation>&apos;&apos;无版本警告&apos;&apos; 数据库</translation>
    </message>
    <message>
        <source>&quot;Use This Instead&quot; Database</source>
        <translation>&apos;&apos;替代为此&apos;&apos; 数据库</translation>
    </message>
    <message>
        <source>Sorting</source>
        <translation>排序</translation>
    </message>
    <message>
        <source>Alphabetically</source>
        <translation>按字母排序</translation>
    </message>
    <message>
        <source>Topologically</source>
        <translation>按拓扑排序</translation>
    </message>
    <message>
        <source>Game location</source>
        <translation>比赛地点</translation>
    </message>
    <message>
        <source>Config location</source>
        <translation>配置位置</translation>
    </message>
    <message>
        <source>Steam mods location</source>
        <translation>Steam 模组位置</translation>
    </message>
    <message>
        <source>Local mods location</source>
        <translation>本地模组位置</translation>
    </message>
    <message>
        <source>Instance folder location (optional)</source>
        <translation>实例文件夹位置（可选）</translation>
    </message>
    <message>
        <source>Backup Settings</source>
        <translation>备份设置</translation>
    </message>
    <message>
        <source>Integration with recent save</source>
        <translation>与最近保存的集成</translation>
    </message>
    <message>
        <source>Auxiliary Metadata DB deletion time limit in seconds. (Delete instantly 0, Never Delete -1)</source>
        <translation>辅助元数据数据库删除时间限制（以秒为单位）。 （立即删除0，永不删除-1）</translation>
    </message>
    <message>
        <source>To enable editing of this time limit, enable the checkbox (Enable editing) on the right.
After a mod is deleted, this is the time we wait until this mod item is deleted from the Auxiliary Metadata DB.
This Auxiliary DB contains info for mod colors, toggled warning, user notes etc.
This basically preserves your mod coloring, user notes etc. for this many seconds after deletion.
(This applies to deletion outside of RimDex too)</source>
        <translation>要启用对此时间限制的编辑，请启用右侧的复选框（启用编辑）。
删除 mod 后，这是我们等待该 mod 项从辅助元数据 DB 中删除的时间。
该辅助数据库包含模组颜色、切换警告、用户注释等信息。
这基本上会在删除后的几秒钟内保留您的模组颜色、用户注释等。
（这也适用于 RimDex 之外的删除）</translation>
    </message>
    <message>
        <source>Sorting Method</source>
        <translation>排序方式</translation>
    </message>
    <message>
        <source>Dependencies Handling Behavior</source>
        <translation>依赖关系处理行为</translation>
    </message>
    <message>
        <source>Use dependency rules for sorting.</source>
        <translation>使用依赖规则进行排序</translation>
    </message>
    <message>
        <source>If enabled, also uses moddependencies as loadTheseBefore, and mods will be sorted such that dependencies are loaded before the dependent mod.</source>
        <translation>如果启用，也会使用moddependencies作为loadTheseBefore，模组会按依赖关系排序，确保依赖项在依赖的模组之前加载。</translation>
    </message>
    <message>
        <source>Prompt user to download dependencies when click in Sort</source>
        <translation>在点击排序时提示用户下载依赖项</translation>
    </message>
    <message>
        <source>XML Parsing Behavior</source>
        <translation>XML 解析行为</translation>
    </message>
    <message>
        <source>When enabled, *ByVersion tags take precedence over the base tags, 
If a matching version tag exists but is empty, the base tag is ignored. 
e.g.(modDependenciesByVersion, loadAfterByVersion, loadBeforeByVersion, incompatibleWithByVersion, descriptionsByVersion)</source>
        <translation>启用后，*ByVersion标签优先于基础标签，
如果存在匹配的版本标签但为空，则忽略基础标签。
例如：(modDependenciesByVersion, loadAfterByVersion, loadBeforeByVersion, incompatibleWithByVersion, descriptionsByVersion)</translation>
    </message>
    <message>
        <source>Case-insensitive About.xml lookup</source>
        <translation>不区分大小写的 About.xml 查找</translation>
    </message>
    <message>
        <source>Enable case-insensitive lookup for About/About.xml.
Some mods use incorrect casing (e.g., about/about.xml) which breaks on
case-sensitive filesystems (Linux). Per the RimWorld modding spec, the
correct path is About/About.xml.
See: https://www.rimworldwiki.com/wiki/Modding_Tutorials/About.xml</source>
        <translation>对 About/About.xml 启用不区分大小写的查找。
某些 mod 使用不正确的大小写（例如 about/about.xml），这会导致
区分大小写的文件系统 (Linux)。根据 RimWorld 改装规范，
正确的路径是 About/About.xml。
请参阅：https://www.rimworldwiki.com/wiki/Modding_Tutorials/About.xml</translation>
    </message>
    <message>
        <source>Mod list options</source>
        <translation>模组列表选项</translation>
    </message>
    <message>
        <source>Notifies to download mods that may be missing in the active modlist</source>
        <translation>提示下载当前启用的模组列表中可能缺失的模组</translation>
    </message>
    <message>
        <source>Notifies and displays the mods that have the same packageid</source>
        <translation>通知并显示具有相同包名的模组</translation>
    </message>
    <message>
        <source>Show recently updated mods indicator</source>
        <translation>显示最近更新的模组指示器</translation>
    </message>
    <message>
        <source>Shows an icon on Steam Workshop mods that were updated within the configured number of days. The update time is refreshed when RimDex refreshes its metadata.</source>
        <translation>在配置的天数内更新的 Steam 创意工坊模组上显示一个图标。当 RimDex 刷新其元数据时，更新时间也会刷新。</translation>
    </message>
    <message>
        <source>Days to consider a mod recently updated:</source>
        <translation>考虑最近更新的模组的天数：</translation>
    </message>
    <message>
        <source>Hides invalid mods, not recommended to enable</source>
        <translation>隐藏无效模组，不建议启用</translation>
    </message>
    <message>
        <source>Inactive Mods Sorting</source>
        <translation>不活跃 Mod 排序</translation>
    </message>
    <message>
        <source>Save inactive mods sort state</source>
        <translation>保存未启用模组排序状态</translation>
    </message>
    <message>
        <source>SteamCMD</source>
        <translation>SteamCMD</translation>
    </message>
    <message>
        <source>Database expiry in seconds for example, 604800 for 7 days. and 0 for no expiry.</source>
        <translation>数据库过期时间（以秒为单位），例如 604800 表示 7 天。 0 表示没有过期时间。</translation>
    </message>
    <message>
        <source>Internal Tools</source>
        <translation>内部工具</translation>
    </message>
    <message>
        <source>Validate downloaded mods</source>
        <translation>验证已经下载的模组</translation>
    </message>
    <message>
        <source>Automatically clear depot cache</source>
        <translation>自动清除仓库缓存</translation>
    </message>
    <message>
        <source>Automatically clear the depot cache before downloading mods through SteamCMD.
This may potentially prevent some issues with downloading mods such as download failures and deleted mods repopulating.</source>
        <translation>在使用 SteamCMD 下载模组前自动清除仓库缓存。
这可能避免在下载模组时出现的一些问题，例如下载失败以及已删除模组重新生成的情况。</translation>
    </message>
    <message>
        <source>SteamCMD installation location</source>
        <translation>SteamCMD安装位置</translation>
    </message>
    <message>
        <source>Clear depot cache</source>
        <translation>清除仓库缓存</translation>
    </message>
    <message>
        <source>Clear the depot cache manually. This may be useful if you encounter issues with downloading mods through SteamCMD.</source>
        <translation>手动清除仓库缓存。当通过SteamCMD下载模组遇到问题时，这一操作可能会非常有用。</translation>
    </message>
    <message>
        <source>Import .acf</source>
        <translation>导入 .acf</translation>
    </message>
    <message>
        <source>Delete .acf</source>
        <translation>删除 .acf</translation>
    </message>
    <message>
        <source>Install SteamCMD</source>
        <translation>安装 SteamCMD</translation>
    </message>
    <message>
        <source>todds</source>
        <translation>托兹</translation>
    </message>
    <message>
        <source>Quality preset</source>
        <translation>质量预设</translation>
    </message>
    <message>
        <source>Optimized - Recommended for RimWorld</source>
        <translation>优化 - 推荐用于 RimWorld</translation>
    </message>
    <message>
        <source>If -p as in path is not specified, path from current active or all mods selection will be used.</source>
        <translation>如果未指定路径中的 -p，则将使用当前活动路径或所有 mods 选择。</translation>
    </message>
    <message>
        <source>When optimizing textures</source>
        <translation>优化纹理时</translation>
    </message>
    <message>
        <source>Optimize active mods only</source>
        <translation>仅优化启用的模组</translation>
    </message>
    <message>
        <source>Optimize all mods</source>
        <translation>优化所有模组</translation>
    </message>
    <message>
        <source>Enable dry-run mode</source>
        <translation>启用模拟运行模式</translation>
    </message>
    <message>
        <source>Overwrite existing optimized textures</source>
        <translation>覆盖已经优化的纹理</translation>
    </message>
    <message>
        <source>Automatically run todds before launching the game</source>
        <translation>启动游戏前自动运行 todds</translation>
    </message>
    <message>
        <source>Text Editor command location</source>
        <translation>文本编辑器命令位置</translation>
    </message>
    <message>
        <source>Theme Settings</source>
        <translation>主题设置</translation>
    </message>
    <message>
        <source>Enable to use theme / stylesheet instead of system Theme</source>
        <translation>&quot;启用主题/样式表而非系统默认主题&quot;</translation>
    </message>
    <message>
        <source>Open Theme Location</source>
        <translation>打开主题路径</translation>
    </message>
    <message>
        <source>Font Settings</source>
        <translation>字体设置</translation>
    </message>
    <message>
        <source>Font Family</source>
        <translation>字体</translation>
    </message>
    <message>
        <source>Font Size</source>
        <translation>字体大小</translation>
    </message>
    <message>
        <source>Reset</source>
        <translation>重置</translation>
    </message>
    <message>
        <source>Language Setting</source>
        <translation>语言设置</translation>
    </message>
    <message>
        <source>Select Language (Restart required to apply changes)</source>
        <translation>选择语言（需要重新启动以应用更改）</translation>
    </message>
    <message>
        <source>RimDex restart required for some settings</source>
        <translation>某些设置需要重新启动 RimDex</translation>
    </message>
    <message>
        <source>Constrain dialogues to main window monitor</source>
        <translation>将对话限制到主窗口监视器</translation>
    </message>
    <message>
        <source>Main Window Launch State</source>
        <translation>主窗口启动状态</translation>
    </message>
    <message>
        <source>Browser Window Launch State</source>
        <translation>浏览器窗口启动状态</translation>
    </message>
    <message>
        <source>Settings Window Launch State</source>
        <translation>设置窗口启动状态</translation>
    </message>
    <message>
        <source>Custom Width:</source>
        <translation>定制宽度：</translation>
    </message>
    <message>
        <source>Custom Height:</source>
        <translation>定制高度：</translation>
    </message>
    <message>
        <source>Advanced</source>
        <translation>高级</translation>
    </message>
    <message>
        <source>Enable debug logging</source>
        <translation>启用调试日志</translation>
    </message>
    <message>
        <source>Enable watchdog file monitor daemon</source>
        <translation>启用文件监护进程</translation>
    </message>
    <message>
        <source>Hide invalid mods when filtering</source>
        <translation>过滤模组时隐藏无效模组</translation>
    </message>
    <message>
        <source>Show duplicate mods warning</source>
        <translation>显示重复模组警告</translation>
    </message>
    <message>
        <source>Check for mod updates on refresh</source>
        <translation>刷新时检查模组更新</translation>
    </message>
    <message>
        <source>Enable Steam client integration</source>
        <translation>启用 Steam 客户端集成</translation>
    </message>
    <message>
        <source>Download missing mods automatically</source>
        <translation>自动下载缺失的模组</translation>
    </message>
    <message>
        <source>Appearance</source>
        <translation>外貌</translation>
    </message>
    <message>
        <source>Render Unity Rich Text in mod descriptions</source>
        <translation>在模组描述中渲染 Unity 富文本</translation>
    </message>
    <message>
        <source>Enable this option to render Unity Rich Text in mod descriptions. Images will not be displayed.</source>
        <translation>启用此选项将在模组描述中渲染 Unity 富文本，图片不会显示。</translation>
    </message>
    <message>
        <source>Update databases on startup</source>
        <translation>启动时更新数据库</translation>
    </message>
    <message>
        <source>Enable this option to automatically update enabled databases when RimDex starts. This will check for updates and download them if available.</source>
        <translation>启用此选项将在 RimDex 启动时自动更新启用的数据库。这将检查更新并在可用时下载它们。</translation>
    </message>
    <message>
        <source>Rentry Auth:</source>
        <translation>Rentry 授权：</translation>
    </message>
    <message>
        <source>Obtain rentry auth code by emailing: support@rentry.co</source>
        <translation>通过发送邮件至 support@rentry.co 获取 Rentry 授权码</translation>
    </message>
    <message>
        <source>GitHub username:</source>
        <translation>Github 用户名</translation>
    </message>
    <message>
        <source>GitHub personal access token:</source>
        <translation>GitHub 个人访问令牌</translation>
    </message>
    <message>
        <source>Edit Game Run Arguments:</source>
        <translation>编辑游戏启动参数：</translation>
    </message>
    <message>
        <source>Maximized</source>
        <translation>最大化</translation>
    </message>
    <message>
        <source>Normal</source>
        <translation>普通</translation>
    </message>
    <message>
        <source>Custom size</source>
        <translation>自定义大小</translation>
    </message>
    <message>
        <source>Delete before update</source>
        <translation>更新前删除模组</translation>
    </message>
    <message>
        <source>This is useful if you want to ensure clean mod updates.</source>
        <translation>如果你想确保模组干净更新，请启用该选项。</translation>
    </message>
    <message>
        <source>Should be like: C:\Program Files (x86)\Steam\steamapps\common\RimWorld</source>
        <translation>路径应类似于：C:\Program Files (x86)\Steam\steamapps\common\RimWorld</translation>
    </message>
    <message>
        <source>Should be like: C:\Users\UserName\AppData\LocalLow\Ludeon Studios\RimWorld by Ludeon Studios\Config</source>
        <translation>路径应类似于：C:\Users\用户名\AppData\LocalLow\Ludeon Studios\RimWorld by Ludeon Studios\Config</translation>
    </message>
    <message>
        <source>Only if you use steam should be like: C:\Program Files (x86)\Steam\steamapps\workshop\content\294100</source>
        <translation>仅在使用Steam时路径应类似于：C:\Program Files (x86)\Steam\steamapps\workshop\content\294100</translation>
    </message>
    <message>
        <source>should be like: C:\Program Files (x86)\Steam\steamapps\common\Rimworld\Mods</source>
        <translation>路径应类似于：C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods</translation>
    </message>
    <message>
        <source>Launch game via Steam protocol (enables Steam overlay)</source>
        <translation>通过 Steam 协议启动游戏（启用 Steam 覆盖）</translation>
    </message>
    <message>
        <source>If enabled, RimDex will launch the game using the Steam protocol (steam://rungameid/294100) instead of directly running the executable. This enables the Steam overlay. Note: This requires Steam to be running and will ignore custom launch arguments.</source>
        <translation>如果启用，RimDex 将使用 Steam 协议 (steam://rungameid/294100) 启动游戏，而不是直接运行可执行文件。这将启用 Steam 覆盖。注意：这需要 Steam 正在运行，并且将忽略自定义启动参数。</translation>
    </message>
    <message>
        <source>Enter launch options using Steam-style syntax with optional %command% placeholder:

 Basic examples (game arguments only):

   -logfile /tmp/log -popupwindow

   -savedatafolder=/path/to/savedata

 Advanced examples (with %command%, env vars, wrappers):

   PROTON_LOG=1 %command%

   gamemoderun %command% -logfile /tmp/log

   DXVK_HUD=1 mangohud %command% -popupwindow

 NOTE: wrapper commands will be ignored on macOS

 NOTE: These arguments are ignored if &apos;Launch game via Steam protocol&apos; is enabled</source>
        <translation>使用 Steam 风格的语法和可选的 %command% 占位符输入启动选项：

 基本示例（仅限游戏参数）：

   -logfile /tmp/log -popupwindow

   -savedatafolder=/路径/到/savedata

 高级示例（使用 %command%、环境变量、包装器）：

   PROTON_LOG=1%命令%

   gamemoderun %command% -logfile /tmp/log

   DXVK_HUD=1 mangohud %command% -popupwindow

 注意：包装命令在 macOS 上将被忽略

 注意：如果启用“通过 Steam 协议启动游戏”，这些参数将被忽略</translation>
    </message>
    <message>
        <source>Enable editing</source>
        <translation>启用编辑</translation>
    </message>
    <message>
        <source>This enables the editing of the time limit for Aux Metadata DB data deletion.</source>
        <translation>这将启用对辅助元数据数据库数据删除时间限制的编辑。</translation>
    </message>
    <message>
        <source>Alphabetical sorting may produce incorrect results with complex mod lists. Topological sorting is recommended.</source>
        <translation>对于复杂的 mod 列表，按字母顺序排序可能会产生不正确的结果。建议采用拓扑排序。</translation>
    </message>
    <message>
        <source>(Deprecated — use Topological instead)</source>
        <translation>（已弃用 - 使用拓扑代替）</translation>
    </message>
    <message>
        <source>To add your own theme / stylesheet 

1) Create a new-folder in &apos;themes&apos; folder in your &apos;RimDex&apos; config folder 
2) Using the default &apos;RimPy&apos; theme copy it to the folder you created 
3) Edit the copied &apos;style.qss&apos; as per your imagination 
4) Start &apos;RimDex&apos; and select your theme from dropdown 
5) Click &apos;ok&apos; to save settings and apply the selected theme 

NOTE 
Name of folder will be used as name of the theme and any invalid theme will be ignored 
</source>
        <translation>要添加自定义主题/样式表

1) 在你的&apos;RimDex&apos;配置文件夹中的&apos;themes&apos;文件夹内新建一个文件夹
2) 将默认的&apos;RimPy&apos;主题复制到你创建的文件夹中
3) 根据你的创意编辑复制的&apos;style.qss&apos;文件
4) 启动&apos;RimDex&apos;并从下拉菜单中选择你的主题
5) 点击&apos;确定&apos;保存设置并应用所选主题 

注意
文件夹名称将用作主题名称，任何无效主题将被忽略
</translation>
    </message>
    <message>
        <source>Apply mod coloring to background instead of text</source>
        <translation>将模组着色应用于背景而不是文本</translation>
    </message>
    <message>
        <source>Min is {MIN_SIZE} and Max is {MAX_SIZE}. Values outside this range will be reset to defaults.</source>
        <translation>最小值为 {MIN_SIZE}，最大值为 {MAX_SIZE}。超出此范围的值将重置为默认值。</translation>
    </message>
    <message>
        <source>Compare mod lists with the recent save file</source>
        <translation>将模组列表与最近的存档文件进行比较</translation>
    </message>
    <message>
        <source>Clear also moves DLC</source>
        <translation>清除也会移动DLC</translation>
    </message>
    <message>
        <source>Custom todds command</source>
        <translation>自定义 todds 命令</translation>
    </message>
    <message>
        <source>eg: {todds_example}</source>
        <translation>例如：{todds_example}</translation>
    </message>
    <message>
        <source>Automatically delete .dds files if no corresponding .png file exists</source>
        <translation>自动删除没有对应 .png 文件的 .dds 文件</translation>
    </message>
    <message>
        <source>This will delete .dds files that are not paired with a .png file,

This checks may take few seconds depending on the number of .dds files present.</source>
        <translation>删除没有对应 .png 文件的 .dds 文件。

根据 .dds 文件数量，检查可能需要几秒钟。</translation>
    </message>
    <message>
        <source>Prefer versioned About.xml tags over base tags</source>
        <translation>优先使用带版本信息的 About.xml 标签，而不是基础标签。</translation>
    </message>
    <message>
        <source>External Tools</source>
        <translation>外部工具</translation>
    </message>
    <message>
        <source>Additional Arguments (Opening Folders)</source>
        <translation>其他参数（打开文件夹）</translation>
    </message>
    <message>
        <source>Additional Arguments (Opening Single File)</source>
        <translation>其他参数（打开单个文件）</translation>
    </message>
    <message>
        <source>Use alternativePackageIds as satisfying dependencies</source>
        <translation>将 alternativePackageIds 视为满足依赖关系</translation>
    </message>
    <message>
        <source>If enabled, an alternativePackageIds entry in About.xml can satisfy a mod&apos;s dependency when the main dependency is missing. 
E.g., &apos;oels.vehiclemapframework&apos;, alternatives: &apos;oels.vehiclemapframework.dev&apos;</source>
        <translation>如果启用，About.xml 中的 alternativePackageIds 条目可以满足模组的依赖关系，即使主要依赖项缺失。
例如，&apos;oels.vehiclemapframework&apos;，替代项：&apos;oels.vehiclemapframework.dev&apos;</translation>
    </message>
    <message>
        <source>Include mod notes in mod name search filter</source>
        <translation>在 Mod 名称搜索过滤器中包含 Mod 注释</translation>
    </message>
    <message>
        <source>This option will include searching mod notes when searching by mod name.</source>
        <translation>此选项将包括在按模组名称搜索时搜索模组注释。</translation>
    </message>
    <message>
        <source>Create backup before RimDex update</source>
        <translation>在 Rimdex 更新之前创建备份</translation>
    </message>
    <message>
        <source>Recommended to keep this enabled as it creates a backup before updating RimDex, This helps prevent any unwanted changes or data getting deleted.</source>
        <translation>建议保持此选项启用，因为在更新 RimDex 之前它会创建备份，这有助于防止任何不必要的更改或数据被删除。</translation>
    </message>
    <message>
        <source>Maximum number of backups to keep:</source>
        <translation>保留的最大备份数量：</translation>
    </message>
</context>
<context>
    <name>SettingsFailureDialog</name>
    <message>
        <source>Open Settings</source>
        <translation>打开设置</translation>
    </message>
    <message>
        <source>Your RimDex settings file is corrupt.
Please choose one of the following options to proceed.</source>
        <translation>你的 RimDex 设置文件已损坏。
请选择以下选项之一继续。</translation>
    </message>
    <message>
        <source>Open Settings Folder</source>
        <translation>打开设置文件夹</translation>
    </message>
    <message>
        <source>Reset Settings</source>
        <translation>重置设置</translation>
    </message>
    <message>
        <source>Exit RimDex</source>
        <translation>退出 RimDex</translation>
    </message>
</context>
<context>
    <name>SteamBrowser</name>
    <message>
        <source>Add Mods by Workshop ID</source>
        <translation>按创意工坊 ID 添加模组</translation>
    </message>
    <message>
        <source>Mod Downloader</source>
        <translation>模组下载器</translation>
    </message>
    <message>
        <source>Add to List</source>
        <translation>添加到列表</translation>
    </message>
    <message>
        <source>Clear List</source>
        <translation>清空列表</translation>
    </message>
    <message>
        <source>Download mod(s) (SteamCMD)</source>
        <translation>下载模组（SteamCMD）</translation>
    </message>
    <message>
        <source>Download mod(s) (Steam app)</source>
        <translation>下载模组（Steam app）</translation>
    </message>
    <message>
        <source>Add to list</source>
        <translation>添加到列表</translation>
    </message>
    <message>
        <source>Enter one or more Workshop IDs (one per line or separated by commas):</source>
        <translation>输入一个或多个创意工坊 ID（每行一个或以逗号分隔）：</translation>
    </message>
    <message>
        <source>No publishedfileid found</source>
        <translation>找不到发布文件 ID</translation>
    </message>
    <message>
        <source>Unable to parse publishedfileid from url, Please check if url is in the correct format</source>
        <translation>无法从链接解析发布文件 ID，请检查链接是否正确的格式</translation>
    </message>
    <message>
        <source>Please reach out to us on Github Issues page or &lt;br&gt;#rimdex-testing on the Rocketman/CAI discord</source>
        <translation>请通过 Github 问题页面或 &lt;br&gt;关于 Rocketman/CAI 不和谐的#rimdex-testing 与我们联系</translation>
    </message>
    <message>
        <source>Add Collection</source>
        <translation>添加合集</translation>
    </message>
    <message>
        <source>How would you like to add the collection?</source>
        <translation>你想如何添加该合集？</translation>
    </message>
    <message>
        <source>You can choose to add all mods from the collection or only the ones you don&apos;t have installed.</source>
        <translation>你可以选择添加合集中的所有模组，或者只添加你没有安装的模组。</translation>
    </message>
    <message>
        <source>Add All Mods</source>
        <translation>添加所有模组</translation>
    </message>
    <message>
        <source>Add Missing Mods</source>
        <translation>添加缺失的模组</translation>
    </message>
    <message>
        <source>SteamCMD downloader</source>
        <translation>SteamCMD 下载器</translation>
    </message>
    <message>
        <source>Empty list of mods returned, unable to add collection to list!</source>
        <translation>返回的模组列表为空，无法将合集添加到列表中！</translation>
    </message>
    <message>
        <source>You already have these mods in your download list!</source>
        <translation>你的下载列表中已经有这些模组！</translation>
    </message>
    <message>
        <source>Skipping the following mods which are already present in your download list!</source>
        <translation>跳过已经存在于你的下载列表中的模组！</translation>
    </message>
</context>
<context>
    <name>SteamcmdInterface</name>
    <message>
        <source>RimDex - SteamCMD setup</source>
        <translation>RimDex - SteamCMD 安装</translation>
    </message>
    <message>
        <source>RimDex was unable to find SteamCMD installed in the configured prefix:&lt;br&gt;</source>
        <translation>RimDex 无法找到安装在配置的前缀中的 SteamCMD：&lt;br&gt;</translation>
    </message>
    <message>
        <source>Do you want to setup SteamCMD?</source>
        <translation>你想设置 SteamCMD 吗？</translation>
    </message>
    <message>
        <source>Depot Cache Cleared</source>
        <translation>仓库缓存已清除</translation>
    </message>
    <message>
        <source>SteamCMD depot cache was already cleared.</source>
        <translation>仓库缓存已清除</translation>
    </message>
    <message>
        <source>SteamCMD depot cache has been cleared.</source>
        <translation>仓库缓存已清除</translation>
    </message>
    <message>
        <source>Re-create Symlink?</source>
        <translation>重新创建符号链接？</translation>
    </message>
    <message>
        <source>An existing symlink already exists. Would you like to delete and re-create the symlink?</source>
        <translation>一个现有的符号链接已经存在。你想删除并重新创建符号链接吗？</translation>
    </message>
    <message>
        <source>The symlink makes SteamCMD download mods to the local mods folder and is required for SteamCMD mod downloads to work correctly.</source>
        <translation>符号链接使 SteamCMD 将模组下载到本地模组文件夹，并确保 SteamCMD 模组下载正常工作。</translation>
    </message>
    <message>
        <source>Existing symlink: {symlink_destination_path}&lt;br&gt;&lt;br&gt;New symlink:&lt;br&gt;[{symlink_source_path}] -&gt; </source>
        <translation>现有符号链接：{symlink_destination_path}&lt;br&gt;&lt;br&gt;新符号链接：&lt;br&gt;[{symlink_source_path}] -&gt;</translation>
    </message>
    <message>
        <source>Existing destination: {symlink_destination_path}&lt;br&gt;&lt;br&gt;New symlink:&lt;br&gt;[{symlink_source_path}] -&gt; </source>
        <translation>现有目标：{symlink_destination_path}&lt;br&gt;&lt;br&gt;新符号链接：&lt;br&gt;[{symlink_source_path}] -&gt;</translation>
    </message>
    <message>
        <source>New symlink:&lt;br&gt;[{symlink_source_path}] -&gt; </source>
        <translation>新符号链接：&lt;br&gt;[{symlink_source_path}] -&gt;</translation>
    </message>
    <message>
        <source>The symlink destination path already exists. Would you like to remove the existing destination and create a new symlink in it&apos;s place?</source>
        <translation>符号链接目标路径已经存在。你想删除现有的目标并创建一个新的符号链接吗？</translation>
    </message>
    <message>
        <source>&amp;No</source>
        <translation>＆不</translation>
    </message>
    <message>
        <source>Create Symlink?</source>
        <translation>创建符号链接？</translation>
    </message>
    <message>
        <source>Do you want to create a symlink?</source>
        <translation>你想创建一个符号链接吗？</translation>
    </message>
    <message>
        <source>&amp;Yes</source>
        <translation>&amp;是</translation>
    </message>
    <message>
        <source>&amp;Don&apos;t Ask Again</source>
        <translation>&amp;不再询问</translation>
    </message>
</context>
<context>
    <name>SteamworksInterface</name>
    <message>
        <source>Steam Not Detected</source>
        <translation>未检测到蒸汽</translation>
    </message>
    <message>
        <source>Steam Integration Unavailable</source>
        <translation>Steam 集成不可用</translation>
    </message>
    <message>
        <source>RimDex could not detect Steam client or it may be unresponsive.&lt;br&gt;&lt;br&gt;Please make sure Steam is installed and running.&lt;br&gt;&lt;br&gt;If you are a Steam user, please check that Steam is running and that you are logged in.&lt;br&gt;&lt;br&gt;Try restarting Steam.</source>
        <translation>RimDex 无法检测到 Steam 客户端，或者可能没有响应。&lt;br&gt;&lt;br&gt;请确保 Steam 已安装并正在运行。&lt;br&gt;&lt;br&gt;如果您是 Steam 用户，请检查 Steam 是否正在运行并且您是否已登录。&lt;br&gt;&lt;br&gt;尝试重新启动 Steam。</translation>
    </message>
    <message>
        <source>If you are still facing issues even after Steam is installed and running, please report this issue to https://github.com/RimDex/RimDex/issues</source>
        <translation>如果在安装并运行 Steam 后您仍然遇到问题，请将此问题报告给 https://github.com/RimDex/RimDex/issues</translation>
    </message>
    <message>
        <source>Snap Steam Detected</source>
        <translation>检测到突然蒸汽</translation>
    </message>
    <message>
        <source>For full Steam support, please install native Steam from the official repository.</source>
        <translation>要获得完整的 Steam 支持，请从官方存储库安装本机 Steam。</translation>
    </message>
    <message>
        <source>Snap Steam is sandboxed and incompatible with Steamworks API</source>
        <translation>Snap Steam 是沙盒的，与 Steamworks API 不兼容</translation>
    </message>
</context>
<context>
    <name>TagEditDialog</name>
    <message>
        <source>Select existing tags and/or enter new tags separated by commas:</source>
        <translation>选择现有标签和/或输入以逗号分隔的新标签：</translation>
    </message>
    <message>
        <source>new-tag, qol, framework</source>
        <translation>新标签、质量、框架</translation>
    </message>
    <message>
        <source>Select all</source>
        <translation>选择全部</translation>
    </message>
    <message>
        <source>Select none</source>
        <translation>不选择</translation>
    </message>
    <message>
        <source>OK</source>
        <translation>好的</translation>
    </message>
    <message>
        <source>Cancel</source>
        <translation>取消</translation>
    </message>
</context>
<context>
    <name>ThemeController</name>
    <message>
        <source>Theme path Error</source>
        <translation>主题路径错误</translation>
    </message>
    <message>
        <source>Stylesheet path does not exist for theme &apos;{theme_name}&apos; Resetting to default theme &apos;{default_theme}&apos;.</source>
        <translation>主题 &apos;{theme_name}&apos; 的样式表路径不存在，重置为默认主题 &apos;{default_theme}&apos;。</translation>
    </message>
    <message>
        <source>Theme Error</source>
        <translation>主题错误</translation>
    </message>
    <message>
        <source>Failed to apply theme: {selected_theme_name},Resetting to default theme: {self.default_theme}</source>
        <translation>应用主题失败：{selected_theme_name}，重置为默认主题：{self.default_theme}</translation>
    </message>
</context>
<context>
    <name>ToddsInterface</name>
    <message>
        <source>ERROR: todds was not found. If you are running from source, please ensure you have followed the correct steps in the {development_guide_url} 

Please reach out to us for support at: {support_url}</source>
        <translation>错误：未找到 todds。如果你是从源码运行，请确保已按照 {development_guide_url} 中的正确步骤操作。

如需帮助，请通过以下地址联系我们：{support_url}</translation>
    </message>
</context>
<context>
    <name>TranslationManagerDialog</name>
    <message>
        <source>RimDex — Translation Manager</source>
        <translation>RimDex — 翻译经理</translation>
    </message>
    <message>
        <source>Language:</source>
        <translation>语言：</translation>
    </message>
    <message>
        <source>All</source>
        <translation>全部</translation>
    </message>
    <message>
        <source>Translation Service</source>
        <translation>翻译服务</translation>
    </message>
    <message>
        <source>Provider:</source>
        <translation>提供商：</translation>
    </message>
    <message>
        <source>API Key:</source>
        <translation>API 密钥：</translation>
    </message>
    <message>
        <source>(not required for Google)</source>
        <translation>（谷歌不需要）</translation>
    </message>
    <message>
        <source>Model:</source>
        <translation>模型：</translation>
    </message>
    <message>
        <source>Concurrency:</source>
        <translation>并发：</translation>
    </message>
    <message>
        <source>Use cache</source>
        <translation>使用缓存</translation>
    </message>
    <message>
        <source>Run All</source>
        <translation>运行全部</translation>
    </message>
    <message>
        <source>Extract (lupdate)</source>
        <translation>提取（lupdate）</translation>
    </message>
    <message>
        <source>Translate</source>
        <translation>翻译</translation>
    </message>
    <message>
        <source>Validate</source>
        <translation>证实</translation>
    </message>
    <message>
        <source>Compile (lrelease)</source>
        <translation>编译（lrelease）</translation>
    </message>
    <message>
        <source>Close</source>
        <translation>关闭</translation>
    </message>
    <message>
        <source>▶ Running all steps…</source>
        <translation>▶ 运行所有步骤...</translation>
    </message>
    <message>
        <source>All steps completed.</source>
        <translation>所有步骤已完成。</translation>
    </message>
    <message>
        <source>✓ All steps completed.</source>
        <translation>✓ 所有步骤均已完成。</translation>
    </message>
    <message>
        <source>—— Step: {step} ——</source>
        <translation>—— 步骤： —— {step}</translation>
    </message>
    <message>
        <source>lupdate: {result}</source>
        <translation>lupdate:  {result}</translation>
    </message>
    <message>
        <source>success</source>
        <translation>成功</translation>
    </message>
    <message>
        <source>failed</source>
        <translation>失败的</translation>
    </message>
    <message>
        <source>No languages found.</source>
        <translation>未找到语言。</translation>
    </message>
    <message>
        <source>translate: done ({t} translated, {f} failed)</source>
        <translation>翻译：完成（{t} 已翻译，{f} 失败）</translation>
    </message>
    <message>
        <source>validate: {n} issue(s)</source>
        <translation>验证：问题） {n}</translation>
    </message>
    <message>
        <source>validate: passed</source>
        <translation>验证：通过</translation>
    </message>
    <message>
        <source>validate: auto-fixed {n} issue(s), rerunning lupdate → translate → validate…</source>
        <translation>验证：自动修复问题），重新运行 lupdate → 已翻译 → 验证... {n}</translation>
    </message>
    <message>
        <source>lrelease: {result}</source>
        <translation>lrelease:  {result}</translation>
    </message>
    <message>
        <source>all</source>
        <translation>全部</translation>
    </message>
    <message>
        <source>Running lupdate for {lang}…</source>
        <translation>为 {lang} 运行 lupdate...</translation>
    </message>
    <message>
        <source>lupdate: success</source>
        <translation>l更新：成功</translation>
    </message>
    <message>
        <source>lupdate: failed</source>
        <translation>l更新：失败</translation>
    </message>
    <message>
        <source>Translating {lang} via {svc}…</source>
        <translation>通过 {svc} 翻译 {lang}...</translation>
    </message>
    <message>
        <source>Translating all {n} languages via {svc}…</source>
        <translation>通过 {svc} 翻译所有 {n} 种语言...</translation>
    </message>
    <message>
        <source>All done — translated: {t}, failed: {f}</source>
        <translation>全部完成 - 翻译：{t}，失败：{f}</translation>
    </message>
    <message>
        <source>Starting {lang}…</source>
        <translation>开始{lang}…</translation>
    </message>
    <message>
        <source>Translated: {t}, failed: {f}</source>
        <translation>已翻译：{t}，失败：{f}</translation>
    </message>
    <message>
        <source>Translation batch failed</source>
        <translation>翻译批次失败</translation>
    </message>
    <message>
        <source>Validating…</source>
        <translation>正在验证...</translation>
    </message>
    <message>
        <source>Issues found:</source>
        <translation>发现问题：</translation>
    </message>
    <message>
        <source>Validation passed.</source>
        <translation>验证通过。</translation>
    </message>
    <message>
        <source>Auto-fixed {n} issue(s).</source>
        <translation>自动修复问题）。 {n}</translation>
    </message>
    <message>
        <source>{n} issue(s), {f} fixed</source>
        <translation>{n} 个问题，{f} 已修复</translation>
    </message>
    <message>
        <source>Compiling {lang}…</source>
        <translation>编译{lang}...</translation>
    </message>
    <message>
        <source>lrelease: success</source>
        <translation>释放：成功</translation>
    </message>
    <message>
        <source>lrelease: failed</source>
        <translation>lrelease：失败</translation>
    </message>
</context>
<context>
    <name>TroubleshootingController</name>
    <message>
        <source>Process complete</source>
        <translation>处理完成</translation>
    </message>
    <message>
        <source>Process complete, wait for steam to complete further process.</source>
        <translation>处理完成，请等待 Steam 完成后续操作。</translation>
    </message>
    <message>
        <source>Steam Launch Failed</source>
        <translation>Steam 启动失败</translation>
    </message>
    <message>
        <source>Steam Workshop Redownload</source>
        <translation>Steam 创意工坊重新下载</translation>
    </message>
    <message>
        <source>Deleted all files in the {config_dir} successfully.</source>
        <translation>已成功删除 {config_dir} 中的所有文件。</translation>
    </message>
    <message>
        <source>No files found in {config_dir} for deletion.</source>
        <translation>在 {config_dir} 中未找到要删除的文件。</translation>
    </message>
    <message>
        <source>Deleted {item} successfully.</source>
        <translation>已成功删除 {item}。</translation>
    </message>
    <message>
        <source>Confirm Changes</source>
        <translation>确认更改</translation>
    </message>
    <message>
        <source>Are you sure you want to apply these changes? This cannot be undone.</source>
        <translation>你确定要应用这些更改吗？此操作无法撤消。</translation>
    </message>
    <message>
        <source>This will delete the selected files. Make sure you have backups if needed.</source>
        <translation>这将删除选定的文件。确保你有备份，如果需要的话。</translation>
    </message>
    <message>
        <source>Confirm Clear</source>
        <translation>确认清除</translation>
    </message>
    <message>
        <source>Successfully deleted all mods and resetting ModsConfig.xml to vanilla state.</source>
        <translation>已成功删除所有模组，并将 ModsConfig.xml 重置为原版状态。</translation>
    </message>
    <message>
        <source>Error</source>
        <translation>错误</translation>
    </message>
    <message>
        <source>Failed to reset ModsConfig.xml.</source>
        <translation>重置 ModsConfig.xml 失败</translation>
    </message>
    <message>
        <source>Export failed</source>
        <translation>导出失败</translation>
    </message>
    <message>
        <source>{mods_config} does not exist, skipping mod export.</source>
        <translation>{mods_config} 不存在，跳过模组导出。</translation>
    </message>
    <message>
        <source>Export Mod List</source>
        <translation>导出模组列表</translation>
    </message>
    <message>
        <source>The selected file is not a valid mod list file.&lt;br&gt;Details: {e}</source>
        <translation>所选文件不是有效的模组列表文件。&lt;br&gt;详细信息：{e}</translation>
    </message>
    <message>
        <source>Successfully deleted Steam&apos;s downloading folder.&lt;br&gt;Restart Steam for the changes to take effect.</source>
        <translation>已成功删除 Steam 的下载文件夹。&lt;br&gt;重新启动 Steam 以使更改生效。</translation>
    </message>
    <message>
        <source>Could not delete Steam&apos;s downloading folder.&lt;br&gt;Please delete it manually: Steam/steamapps/downloading&lt;br&gt;Details: {e}</source>
        <translation>无法删除 Steam 的下载文件夹。&lt;br&gt;请手动删除：Steam/steamapps/downloading&lt;br&gt;详细信息：{e}</translation>
    </message>
    <message>
        <source>No installed games found in this Steam library folder.&lt;br&gt;You may have games installed in a different Steam library folder or drive.</source>
        <translation>在此 Steam 库文件夹中找不到已安装的游戏。&lt;br&gt;您可能在其他 Steam 库文件夹或驱动器中安装了游戏。</translation>
    </message>
    <message>
        <source>This will verify all {len} games in your Steam library.&lt;br&gt;This may take a while. Continue?</source>
        <translation>这将验证您的 Steam 库中的所有 {len} 游戏。&lt;br&gt;这可能需要一段时间。继续？</translation>
    </message>
    <message>
        <source>Steam will now verify {len} games.&lt;br&gt;You can monitor progress in the Steam client.</source>
        <translation>Steam 现在将验证 {len} 个游戏。&lt;br&gt;您可以在 Steam 客户端中监控进度。</translation>
    </message>
    <message>
        <source>Could not repair Steam library.&lt;br&gt;Please verify your games manually through Steam.&lt;br&gt;Details: {e}</source>
        <translation>无法修复 Steam 库。&lt;br&gt;请通过 Steam 手动验证您的游戏。&lt;br&gt;详细信息：{e}</translation>
    </message>
    <message>
        <source>ACF File Not Found</source>
        <translation>未找到 ACF 文件</translation>
    </message>
    <message>
        <source>Could not find the Steam Workshop ACF file at:&lt;br&gt;{acf_path}</source>
        <translation>在以下位置找不到 Steam 创意工坊 ACF 文件：&lt;br&gt;{acf_path}</translation>
    </message>
    <message>
        <source>This will remove stale workshop entries from the ACF metadata file for mods that no longer exist on disk.&lt;br&gt;&lt;br&gt;A backup will be created before any changes are made.&lt;br&gt;&lt;br&gt;Continue?</source>
        <translation>这将从 ACF 元数据文件中删除磁盘上不再存在的模组的陈旧创意工坊条目。&lt;br&gt;&lt;br&gt;在进行任何更改之前将创建备份。&lt;br&gt;&lt;br&gt;继续吗？</translation>
    </message>
    <message>
        <source>Clean Orphaned Workshop Items</source>
        <translation>清理孤儿工坊物品</translation>
    </message>
    <message>
        <source>Cleanup Complete</source>
        <translation>清理完成</translation>
    </message>
    <message>
        <source>Removed {count} orphaned workshop entries.</source>
        <translation>删除了 {count} 个孤立的创意工坊条目。</translation>
    </message>
    <message>
        <source>No Orphans Found</source>
        <translation>未发现孤儿</translation>
    </message>
    <message>
        <source>No orphaned workshop entries were found. The ACF file is clean.</source>
        <translation>未找到孤立的研讨会条目。 ACF 文件是干净的。</translation>
    </message>
    <message>
        <source>Cleanup Failed</source>
        <translation>清理失败</translation>
    </message>
    <message>
        <source>Failed to clean orphaned workshop items.</source>
        <translation>无法清理废弃的工坊物品。</translation>
    </message>
    <message>
        <source>Location Error</source>
        <translation>路径错误</translation>
    </message>
    <message>
        <source>Confirm Export</source>
        <translation>确认导出</translation>
    </message>
    <message>
        <source>Could not automatically start game installation through Steam.&lt;br&gt;&lt;br&gt;Please manually verify/install the game through Steam.</source>
        <translation>无法通过 Steam 自动启动游戏安装。&lt;br&gt;&lt;br&gt;请通过 Steam 手动验证/安装游戏。</translation>
    </message>
    <message>
        <source>Deleted all files in the Steam mods directory.&lt;br&gt;&lt;br&gt; Trying to restart Steam to trigger automatic redownload of subscribed mods.</source>
        <translation>删除了 Steam mods 目录中的所有文件。&lt;br&gt;&lt;br&gt; 尝试重新启动 Steam 以触发订阅 mods 的自动重新下载。</translation>
    </message>
    <message>
        <source>Mods have been deleted. Please restart Steam to trigger automatic redownload of subscribed mods.&lt;br&gt;&lt;br&gt;If mods don&apos;t download automatically, try:&lt;br&gt;1. Restart Steam&lt;br&gt;2. Verify game files in Steam&lt;br&gt;3. Visit the Workshop page of each mod</source>
        <translation>模组已被删除。请重新启动 Steam 以触发自动重新下载已订阅的模组。&lt;br&gt;&lt;br&gt;如果模组未自动下载，请尝试：&lt;br&gt;1.重新启动 Steam&lt;br&gt;2。验证 Steam 中的游戏文件&lt;br&gt;3。访问每个模组的创意工坊页面</translation>
    </message>
    <message>
        <source>Are you sure you want to delete all mods?&lt;br&gt;&lt;br&gt;WARNING: This will permanently delete all mods in your Mods folder and reset to vanilla state.</source>
        <translation>您确定要删除所有模组吗？&lt;br&gt;&lt;br&gt;警告：这将永久删除 Mods 文件夹中的所有模组并重置为普通状态。</translation>
    </message>
    <message>
        <source>Export current mod list to file?</source>
        <translation>导出当前模组列表到文件？</translation>
    </message>
    <message>
        <source>Failed to export mod list.</source>
        <translation>导出模组列表失败</translation>
    </message>
    <message>
        <source>Import failed</source>
        <translation>导入失败</translation>
    </message>
    <message>
        <source>{mods_config} does not exist, skipping mod import.</source>
        <translation>{mods_config} 不存在，跳过模组导入。</translation>
    </message>
    <message>
        <source>Import Mod List</source>
        <translation>导入模组列表</translation>
    </message>
    <message>
        <source>Confirm Import</source>
        <translation>确认导入</translation>
    </message>
    <message>
        <source>Import mod list from file?</source>
        <translation>从文件导入模组列表？</translation>
    </message>
    <message>
        <source>This will overwrite your current mod list.</source>
        <translation>这将覆盖你当前的模组列表。</translation>
    </message>
    <message>
        <source>Failed to import mod list</source>
        <translation>导入模组列表失败</translation>
    </message>
    <message>
        <source>Cache Cleared</source>
        <translation>清除缓存</translation>
    </message>
    <message>
        <source>Cache Clear</source>
        <translation>清除缓存</translation>
    </message>
    <message>
        <source>Steam&apos;s downloading folder is already empty.</source>
        <translation>Steam 的下载文件夹已经是空的。</translation>
    </message>
    <message>
        <source>Cache Clear Failed</source>
        <translation>清除缓存失败</translation>
    </message>
    <message>
        <source>Steam Action Failed</source>
        <translation>Steam 操作失败</translation>
    </message>
    <message>
        <source>No Games Found</source>
        <translation>找不到游戏</translation>
    </message>
    <message>
        <source>Confirm Library Repair</source>
        <translation>确认修复库</translation>
    </message>
    <message>
        <source>Library Repair Started</source>
        <translation>库修复已开始</translation>
    </message>
    <message>
        <source>Path not set, Please check your settings and Try again.</source>
        <translation>路径未设置，请检查你的设置并重试。</translation>
    </message>
    <message>
        <source>Process failed</source>
        <translation>处理失败</translation>
    </message>
    <message>
        <source>Could not process: {item}</source>
        <translation>无法处理：{item}</translation>
    </message>
    <message>
        <source>Failed to process item: {item} due to the following error: {e}</source>
        <translation>处理项目失败：{item} 由于以下错误：{e}</translation>
    </message>
    <message>
        <source>Steam user Check failed</source>
        <translation>Steam 用户检查失败</translation>
    </message>
    <message>
        <source>You are not a Steam user, or Path not set, Please check settings and try again.</source>
        <translation>你不是 Steam 用户，或者路径未设置，请检查设置并重试。</translation>
    </message>
    <message>
        <source>Error: {e}</source>
        <translation>错误：{e}</translation>
    </message>
</context>
<context>
    <name>TroubleshootingDialog</name>
    <message>
        <source>Game Files Recovery</source>
        <translation>游戏文件恢复</translation>
    </message>
    <message>
        <source>If you&apos;re experiencing issues with your game, you can try the following recovery options. Steam will automatically redownload any deleted files on next launch.</source>
        <translation>如果你在游戏中遇到问题，可以尝试以下恢复选项，Steam 将在下次启动时自动重新下载已删除的文件。</translation>
    </message>
    <message>
        <source>Reset game files (Preserves local mods, deletes and redownloads game files)</source>
        <translation>重置游戏文件（保留本地模组，删除并重新下载游戏文件）</translation>
    </message>
    <message>
        <source>Deletes and redownloads game files but keeps your local mods intact.</source>
        <translation>删除并重新下载游戏文件，但保留你的本地模组。</translation>
    </message>
    <message>
        <source>Reset Steam Workshop mods (Deletes and redownloads all Steam mods)</source>
        <translation>重置Steam创意工坊模组（删除并重新下载所有Steam模组）</translation>
    </message>
    <message>
        <source>Deletes all Steam Workshop mods and triggers redownload.</source>
        <translation>删除所有Steam创意工坊模组并重新下载。</translation>
    </message>
    <message>
        <source>Reset mod configurations (Preserves ModsConfig.xml and Prefs.xml)</source>
        <translation>重置模组配置（保留ModsConfig.xml和Prefs.xml）</translation>
    </message>
    <message>
        <source>Deletes mod configuration files except ModsConfig.xml and Prefs.xml.</source>
        <translation>删除模组配置文件，但保留 ModsConfig.xml 和 Prefs.xml。</translation>
    </message>
    <message>
        <source>Reset game configurations (ModsConfig.xml, Prefs.xml, KeyPrefs.xml)*</source>
        <translation>重置游戏配置（ModsConfig.xml, Prefs.xml, KeyPrefs.xml）</translation>
    </message>
    <message>
        <source>Deletes game configuration files including ModsConfig.xml, Prefs.xml, and KeyPrefs.xml.</source>
        <translation>删除游戏配置文件，包括 ModsConfig.xml、Prefs.xml 和 KeyPrefs.xml。</translation>
    </message>
    <message>
        <source>After resetting game configurations, launch the game directly through Steam to regenerate ModsConfig.xml, then restart RimDex.</source>
        <translation>重置游戏配置后，请通过 Steam 直接启动游戏以重新生成 ModsConfig.xml，然后重新启动 RimDex。</translation>
    </message>
    <message>
        <source>Apply Recovery</source>
        <translation>应用恢复选项</translation>
    </message>
    <message>
        <source>Cancel</source>
        <translation>取消</translation>
    </message>
    <message>
        <source>Mod Configuration Options</source>
        <translation>模组配置选项</translation>
    </message>
    <message>
        <source>Manage your mod configurations and load order. These options help you organize and share your mod setup.</source>
        <translation>管理你的模组配置和加载顺序。这些选项可帮助你组织和分享模组设置。</translation>
    </message>
    <message>
        <source>Save your current mod list to a .xml file to share with others.</source>
        <translation>将当前的模组列表保存为 .xml 文件以便与他人分享。</translation>
    </message>
    <message>
        <source>Clean Orphaned Mods</source>
        <translation>清理孤立的模组</translation>
    </message>
    <message>
        <source>Remove stale workshop entries for mods no longer on disk</source>
        <translation>删除磁盘上不再存在的模组的陈旧创意工坊条目</translation>
    </message>
    <message>
        <source>Export Mod List</source>
        <translation>导出模组列表</translation>
    </message>
    <message>
        <source>Export your current mod list to a file</source>
        <translation>将当前模组列表导出到文件</translation>
    </message>
    <message>
        <source>Import a mod list in .xml format from another player</source>
        <translation>从其他玩家导入 .xml 格式的模组列表</translation>
    </message>
    <message>
        <source>Import Mod List</source>
        <translation>导入模组列表</translation>
    </message>
    <message>
        <source>Import a mod list from a file</source>
        <translation>从文件导入模组列表</translation>
    </message>
    <message>
        <source>Delete all mods and reset to vanilla state</source>
        <translation>删除所有模组并重置为原版状态</translation>
    </message>
    <message>
        <source>Steam Utilities</source>
        <translation>Steam 工具</translation>
    </message>
    <message>
        <source>Delete Steam&apos;s downloading folder to fix download issues</source>
        <translation>删除 Steam 下载文件夹以修复下载问题</translation>
    </message>
    <message>
        <source>Check and repair RimWorld game files</source>
        <translation>检查并修复 RimWorld 游戏文件</translation>
    </message>
    <message>
        <source>Verify integrity of all installed Steam games</source>
        <translation>验证所有已安装 Steam 游戏的完整性</translation>
    </message>
    <message>
        <source>Warning: These operations will delete selected files permanently!</source>
        <translation>警告：这些操作将永久删除所选文件！</translation>
    </message>
    <message>
        <source>Export List</source>
        <translation>导出列表</translation>
    </message>
    <message>
        <source>Import List</source>
        <translation>导入列表</translation>
    </message>
    <message>
        <source>Reset to Vanilla</source>
        <translation>重置为原版</translation>
    </message>
    <message>
        <source>This will delete all mods in your Mods folder and reset to vanilla state</source>
        <translation>这将删除你的模组文件夹中的所有模组并重置为原版状态</translation>
    </message>
    <message>
        <source>Clear All Mods</source>
        <translation>清除所有模组</translation>
    </message>
    <message>
        <source>Steam-specific utilities to help resolve download and game file issues.</source>
        <translation>Steam 专用工具，帮助解决下载和游戏文件问题。</translation>
    </message>
    <message>
        <source>Clear Download Cache</source>
        <translation>清理下载缓存</translation>
    </message>
    <message>
        <source>Verify Game Files</source>
        <translation>验证游戏文件</translation>
    </message>
    <message>
        <source>Repair Steam Library</source>
        <translation>修复 Steam 库</translation>
    </message>
</context>
<context>
    <name>UIBaseMixin</name>
    <message>
        <source>Do nothing and exit</source>
        <translation>不执行任何操作并退出</translation>
    </message>
</context>
<context>
    <name>UpdateManager</name>
    <message>
        <source>RimDex update found</source>
        <translation>检测到 RimDex 更新</translation>
    </message>
    <message>
        <source>An update to RimDex has been released: {latest_tag_name}</source>
        <translation>RimDex 的更新已发布： {latest_tag_name}</translation>
    </message>
    <message>
        <source>Downloading RimDex {tag_name} release...</source>
        <translation>下载 RimDex {tag_name} 版本...</translation>
    </message>
    <message>
        <source>Download failed</source>
        <translation>下载失败</translation>
    </message>
    <message>
        <source>Failed to download the update.</source>
        <translation>下载更新失败。</translation>
    </message>
    <message>
        <source>Extraction failed</source>
        <translation>提取失败</translation>
    </message>
    <message>
        <source>Failed to extract the downloaded update.</source>
        <translation>无法提取下载的更新。</translation>
    </message>
    <message>
        <source>Launch failed</source>
        <translation>启动失败</translation>
    </message>
    <message>
        <source>Failed to launch the update script.</source>
        <translation>无法启动更新脚本。</translation>
    </message>
    <message>
        <source>Creating backup... (this may take several minutes)</source>
        <translation>正在创建备份...（这可能需要几分钟）</translation>
    </message>
    <message>
        <source>Update downloaded</source>
        <translation>更新已下载</translation>
    </message>
    <message>
        <source>Update failed</source>
        <translation>更新失败</translation>
    </message>
    <message>
        <source>An unexpected error occurred during the update process.</source>
        <translation>更新过程中发生意外错误。</translation>
    </message>
    <message>
        <source>Update skipped</source>
        <translation>更新已跳过</translation>
    </message>
    <message>
        <source>You are running from Python interpreter.</source>
        <translation>您正在从 Python 解释器运行。</translation>
    </message>
    <message>
        <source>Skipping update check...</source>
        <translation>跳过更新检查...</translation>
    </message>
    <message>
        <source>Unknown Version Detected</source>
        <translation>检测到未知版本</translation>
    </message>
    <message>
        <source>Could not find version Information of RimDex, This may indicate that the application is not an offical release and may be a custom build.</source>
        <translation>找不到 RimDex 的版本信息，这可能表明该应用程序不是官方版本，可能是自定义版本。</translation>
    </message>
    <message>
        <source>Are you sure you want to still update anyway?</source>
        <translation>您确定仍要更新吗？</translation>
    </message>
    <message>
        <source>You are running RimDex {current_version}&lt;br&gt;Do you want to update now?</source>
        <translation>您正在运行 RimDex {current_version}&lt;br&gt;您想立即更新吗？</translation>
    </message>
    <message>
        <source>RimDex Update Error</source>
        <translation>RimDex 更新错误</translation>
    </message>
    <message>
        <source>Failed to connect to GitHub API: {error}</source>
        <translation>无法连接到 GitHub API： {error}</translation>
    </message>
    <message>
        <source>Do you want to proceed with the update?</source>
        <translation>你想继续更新吗？</translation>
    </message>
    <message>
        <source>&lt;br&gt;Successfully retrieved latest release.&lt;br&gt;The update will be installed from: {update_source_path}</source>
        <translation>&lt;br&gt;已成功检索最新版本。&lt;br&gt;将从以下位置安装更新：{update_source_path}</translation>
    </message>
    <message>
        <source>Backup failed</source>
        <translation>备份失败</translation>
    </message>
    <message>
        <source>Failed to create a backup before updating.</source>
        <translation>更新前无法创建备份。</translation>
    </message>
    <message>
        <source>Unable to retrieve latest release information</source>
        <translation>无法检索最新版本信息</translation>
    </message>
    <message>
        <source>Please check your internet connection and try again, You can also check &apos;https://github.com/RimDex/RimDex/releases&apos; directly.</source>
        <translation>请检查您的互联网连接并重试，您也可以直接检查“https://github.com/RimDex/RimDex/releases”。</translation>
    </message>
</context>
<context>
    <name>UseThisInsteadPanel</name>
    <message>
        <source>RimDex - Replacements found for Workshop mods</source>
        <translation>RimDex - 已找到创意工坊模组的替代项</translation>
    </message>
    <message>
        <source>There are replacements available for Workshop mods!</source>
        <translation>已有可替代的模组可用于创意工坊模组！</translation>
    </message>
    <message>
        <source>The following table displays Workshop mods with suggested replacements according to the &quot;Use This Instead&quot; database, grouped by replacement mod.</source>
        <translation>下表显示了根据“使用此替代”数据库提供的建议替换的创意工坊模组，并按替换模组分组。</translation>
    </message>
    <message>
        <source>Do nothing and exit</source>
        <translation>不执行任何操作并退出</translation>
    </message>
    <message>
        <source>Select</source>
        <translation>选择</translation>
    </message>
    <message>
        <source>Select all Originals</source>
        <translation>选择所有原件</translation>
    </message>
    <message>
        <source>Select all Replacements</source>
        <translation>选择所有替换件</translation>
    </message>
    <message>
        <source>Installed</source>
        <translation>已安装</translation>
    </message>
    <message>
        <source>Not Installed</source>
        <translation>未安装</translation>
    </message>
    <message>
        <source>Group {0}</source>
        <translation>分组 {0}</translation>
    </message>
    <message>
        <source>Original</source>
        <translation>原始</translation>
    </message>
    <message>
        <source>Replacement [{0}]</source>
        <translation>替换 [{0}]</translation>
    </message>
</context>
<context>
    <name>WorkshopModUpdaterPanel</name>
    <message>
        <source>RimDex - Updates found for Workshop mods</source>
        <translation>RimDex - 找到创意工坊模组的更新</translation>
    </message>
    <message>
        <source>There are updates available for Workshop mods!</source>
        <translation>创意工坊模组有更新！</translation>
    </message>
    <message>
        <source>Update Mods with SteamCMD</source>
        <translation>使用 SteamCMD 更新模组</translation>
    </message>
    <message>
        <source>Update Mods with Steam</source>
        <translation>使用 Steam 更新模组</translation>
    </message>
    <message>
        <source>
The following table displays Workshop mods available for update from Steam.</source>
        <translation>下表显示了可从 Steam 更新的创意工坊模组。</translation>
    </message>
</context>
<context>
    <name>_UploadLogDialog</name>
    <message>
        <source>Uploading Log...</source>
        <translation>上传日志...</translation>
    </message>
    <message>
        <source>Log Upload Successful</source>
        <translation>日志上传成功</translation>
    </message>
    <message>
        <source>Log file uploaded successfully! Copied URL to clipboard.</source>
        <translation>日志文件上传成功！已将链接复制到剪贴板。</translation>
    </message>
    <message>
        <source>Log Upload Failed</source>
        <translation>日志上传失败</translation>
    </message>
    <message>
        <source>Log file upload failed!</source>
        <translation>日志文件上传失败！</translation>
    </message>
    <message>
        <source>Please check your internet connection and try again.</source>
        <translation>请检查你的互联网连接并重试。</translation>
    </message>
</context>
<context>
    <name>check_if_pfids_blacklisted</name>
    <message>
        <source>Download blacklisted mods</source>
        <translation>下载黑名单模组</translation>
    </message>
    <message>
        <source>Skip blacklisted mods</source>
        <translation>跳过黑名单模组</translation>
    </message>
</context>
<context>
    <name>copy_to_clipboard_safely</name>
    <message>
        <source>Failed to copy to clipboard.</source>
        <translation>复制到剪贴板失败。</translation>
    </message>
    <message>
        <source>RimDex failed to copy the text to your clipboard. Please copy it manually.</source>
        <translation>RimDex 无法将文本复制到你的剪贴板。请手动复制。</translation>
    </message>
</context>
<context>
    <name>find_circular_dependencies</name>
    <message>
        <source>Unable to Sort</source>
        <translation>无法排序</translation>
    </message>
    <message>
        <source>RimDex found circular dependencies in your mods list. Please see the details for dependency loops.</source>
        <translation>RimDex 在你的模组列表中发现了循环依赖。请查看详细信息以了解循环依赖。</translation>
    </message>
</context>
<context>
    <name>launch_game_process</name>
    <message>
        <source>Game launch failed</source>
        <translation>游戏启动失败</translation>
    </message>
    <message>
        <source>Unable to launch RimWorld</source>
        <translation>无法启动 RimWorld</translation>
    </message>
    <message>
        <source>RimDex could not start RimWorld as the game folder is empty or invalid: [{game_install_path}] Please check that the game folder is properly set and that the RimWorld executable exists in it.</source>
        <translation>RimDex 无法启动 RimWorld 因为游戏文件夹为空或无效：[{game_install_path}] 请检查游戏文件夹是否正确设置，并且 RimWorld 可执行文件是否存在。</translation>
    </message>
    <message>
        <source>Invalid game folder</source>
        <translation>无效的游戏路径</translation>
    </message>
    <message>
        <source>RimDex could not validate the RimWorld executable in the specified folder: {game_install_path}. Please check that this directory is correct and contains a valid RimWorld game executable.</source>
        <translation>RimDex 无法验证指定文件夹中的 RimWorld 可执行文件：{game_install_path}。请检查该目录是否正确并包含有效的 RimWorld 游戏可执行文件。</translation>
    </message>
</context>
<context>
    <name>rmtree</name>
    <message>
        <source>RimDex tried to remove a directory that does not exist.</source>
        <translation>RimDex 尝试删除一个不存在的目录。</translation>
    </message>
    <message>
        <source>Directory does not exist: {path}</source>
        <translation>目录不存在：{path}</translation>
    </message>
    <message>
        <source>Failed to remove directory</source>
        <translation>无法删除目录</translation>
    </message>
    <message>
        <source>RimDex tried to remove a directory that is not a directory.</source>
        <translation>RimDex 尝试删除一个不是目录的目录。</translation>
    </message>
    <message>
        <source>Path is not a directory: {path}</source>
        <translation>路径不是目录：{path}</translation>
    </message>
    <message>
        <source>An OSError occurred while trying to remove a directory.</source>
        <translation>在尝试删除目录时发生 OSError。</translation>
    </message>
    <message>
        <source>{e.strerror} occurred at {e.filename} with error code {error_code}.</source>
        <translation>{e.strerror} 在 {e.filename} 发生，错误代码 {error_code}。</translation>
    </message>
</context>
<context>
    <name>self._panel</name>
    <message>
        <source>Failed to export to file</source>
        <translation>无法导出到文件</translation>
    </message>
    <message>
        <source>Failed to export active mods to file:</source>
        <translation>无法将活动模组导出到文件：</translation>
    </message>
    <message>
        <source>Important</source>
        <translation>重要的</translation>
    </message>
    <message>
        <source>You will need to redo Rentry import again after downloads complete.&lt;br&gt;&lt;br&gt;If there missing mods after download completes, they will be shown inside the missing mods panel.&lt;br&gt;&lt;br&gt;If RimDex is still not able to download some mods, It&apos;s due to the mod data not being available in both Rentry link and steam database.</source>
        <translation>下载完成后，您需要再次重新导入Rentry。&lt;br&gt;&lt;br&gt;如果下载完成后缺少模组，它们将显示在缺少模组面板中。&lt;br&gt;&lt;br&gt;如果RimDex仍然无法下载某些模组，这是因为Rentry链接和steam数据库中都没有模组数据。</translation>
    </message>
    <message>
        <source>Steam client integration not set up</source>
        <translation>Steam 客户端集成未设置</translation>
    </message>
    <message>
        <source>Steam client integration is not set up. Please set it up to download mods using Steam</source>
        <translation>Steam 客户端集成未设置。请设置为使用 Steam 下载模组</translation>
    </message>
    <message>
        <source>Download Rentry Mods</source>
        <translation>下载租赁模组</translation>
    </message>
    <message>
        <source>Please select a download method.</source>
        <translation>请选择下载方式。</translation>
    </message>
    <message>
        <source>Select which method you want to use to download missing Rentry mods.</source>
        <translation>选择您要使用哪种方法来下载缺少的 Rentry mod。</translation>
    </message>
    <message>
        <source>Export active mod list</source>
        <translation>导出活动模组列表</translation>
    </message>
    <message>
        <source>Copied active mod list report to clipboard...</source>
        <translation>已将活动模组列表报告复制到剪贴板...</translation>
    </message>
    <message>
        <source>Click &quot;Show Details&quot; to see the full report!</source>
        <translation>点击“显示详细信息”查看完整报告！</translation>
    </message>
    <message>
        <source>Report too long</source>
        <translation>报告太长</translation>
    </message>
    <message>
        <source>Even the first mod exceeds the 200,000 character limit.</source>
        <translation>即使第一个 mod 也超过了 200,000 字符的限制。</translation>
    </message>
    <message>
        <source>Cannot upload this report to Rentry.co.</source>
        <translation>无法将此报告上传至 Rentry.co。</translation>
    </message>
    <message>
        <source>The mod list report exceeds 200,000 characters.</source>
        <translation>Mod 列表报告超过 200,000 个字符。</translation>
    </message>
    <message>
        <source>Rentry.co may reject uploads that are too long. Would you like to truncate the report to the first {max_mods} mods or cancel the upload?</source>
        <translation>Rentry.co 可能会拒绝太长的上传。您想要将报告截断到前 {max_mods} 个模组或取消上传吗？</translation>
    </message>
    <message>
        <source>Truncate to the first {max_mods} mods</source>
        <translation>截断到第一个 {max_mods} 个 mod</translation>
    </message>
    <message>
        <source>Uploaded active mod list</source>
        <translation>已上传的活动模组列表</translation>
    </message>
    <message>
        <source>Uploaded active mod list report to Rentry.co! The URL has been copied to your clipboard:&lt;br&gt;&lt;br&gt;{url}</source>
        <translation>已将活跃模组列表报告上传至 Rentry.co！该网址已复制到您的剪贴板：&lt;br&gt;&lt;br&gt;{url}</translation>
    </message>
    <message>
        <source>Failed to upload</source>
        <translation>上传失败</translation>
    </message>
    <message>
        <source>Failed to upload exported active mod list to Rentry.co</source>
        <translation>无法将导出的活动模组列表上传到 Rentry.co</translation>
    </message>
    <message>
        <source>Import from RimWorld Save File</source>
        <translation>从 RimWorld 保存文件导入</translation>
    </message>
    <message>
        <source>RimWorld save (*.rws);;All files (*.*)</source>
        <translation>RimWorld 保存 (*.rws);;所有文件 (*.*)</translation>
    </message>
    <message>
        <source>Confirm ACF import</source>
        <translation>确认 ACF 导入</translation>
    </message>
    <message>
        <source>This will replace your current steamcmd .acf file</source>
        <translation>这将替换您当前的 steamcmd .acf 文件</translation>
    </message>
    <message>
        <source>Are you sure you want to import .acf? This only works for steamcmd</source>
        <translation>您确定要导入 .acf 吗？这只适用于 steamcmd</translation>
    </message>
    <message>
        <source>Import .acf</source>
        <translation>导入.acf</translation>
    </message>
    <message>
        <source>Export Error</source>
        <translation>导出错误</translation>
    </message>
    <message>
        <source>ACF file not found at: {acf_path}</source>
        <translation>在以下位置找不到 ACF 文件：{acf_path}</translation>
    </message>
    <message>
        <source>Export Success</source>
        <translation>导出成功</translation>
    </message>
    <message>
        <source>Successfully exported ACF to {file_path}</source>
        <translation>已成功将 ACF 导出到 {file_path}</translation>
    </message>
    <message>
        <source>Export failed: Permission denied - check file permissions</source>
        <translation>导出失败：权限被拒绝 - 检查文件权限</translation>
    </message>
    <message>
        <source>Export failed: {e}</source>
        <translation>导出失败：{e}</translation>
    </message>
    <message>
        <source>Reset SteamCMD ACF data file</source>
        <translation>重置SteamCMD ACF数据文件</translation>
    </message>
    <message>
        <source>Are you sure you want to reset SteamCMD ACF data file?</source>
        <translation>您确定要重置 SteamCMD ACF 数据文件吗？</translation>
    </message>
    <message>
        <source>This file is created and used by steamcmd to track mod informaton, This action cannot be undone.</source>
        <translation>此文件由 steamcmd 创建并使用来跟踪 mod 信息，此操作无法撤消。</translation>
    </message>
    <message>
        <source>Successfully deleted SteamCMD ACF data file: {steamcmd_appworkshop_acf_path}</source>
        <translation>已成功删除 SteamCMD ACF 数据文件：{steamcmd_appworkshop_acf_path}</translation>
    </message>
    <message>
        <source>ACF data file will be recreated when you download mods using steamcmd next time.</source>
        <translation>当您下次使用 steamcmd 下载模组时，将重新创建 ACF 数据文件。</translation>
    </message>
    <message>
        <source>SteamCMD ACF data file does not exist</source>
        <translation>SteamCMD ACF 数据文件不存在</translation>
    </message>
    <message>
        <source>ACf file does not exist. It will be created when you download mods using steamcmd.</source>
        <translation>ACf 文件不存在。当您使用 steamcmd 下载模组时将会创建它。</translation>
    </message>
    <message>
        <source>Checking Steam Workshop mods for updates...</source>
        <translation>正在检查 Steam 创意工坊模组的更新...</translation>
    </message>
    <message>
        <source>No Workshop mods to check for updates</source>
        <translation>没有创意工坊模组来检查更新</translation>
    </message>
    <message>
        <source>Unable to check for updates</source>
        <translation>无法检查更新</translation>
    </message>
    <message>
        <source>RimDex was unable to check your Workshop mods for updates.</source>
        <translation>RimDex 无法检查您的创意工坊模组是否有更新。</translation>
    </message>
    <message>
        <source>Update check partially completed</source>
        <translation>更新检查部分完成</translation>
    </message>
    <message>
        <source>{failed} out of {total} Workshop mods could not be checked for updates.</source>
        <translation>无法检查更新的 {failed} 个创意工坊模组（共 {total} 个）。</translation>
    </message>
    <message>
        <source>All Workshop mods appear to be up to date!</source>
        <translation>所有创意工坊模组似乎都是最新的！</translation>
    </message>
    <message>
        <source>Steam Client Integration is disabled</source>
        <translation>Steam 客户端集成已禁用</translation>
    </message>
    <message>
        <source>This feature requires Steam Client Integration to be enabled in Settings.&lt;br&gt;&lt;br&gt;Please enable Steam Client Integration if you own the game on Steam.</source>
        <translation>此功能需要在“设置”中启用 Steam 客户端集成。&lt;br&gt;&lt;br&gt;如果您在 Steam 上拥有该游戏，请启用 Steam 客户端集成。</translation>
    </message>
    <message>
        <source>RimDex</source>
        <translation>环德克斯</translation>
    </message>
    <message>
        <source>No PublishedFileIds were supplied in operation.</source>
        <translation>操作中未提供 PublishedFileIds。</translation>
    </message>
    <message>
        <source>Please add mods to list before attempting to download.</source>
        <translation>请在尝试下载之前将模组添加到列表中。</translation>
    </message>
    <message>
        <source>RimDex - SteamCMD setup</source>
        <translation>RimDex - SteamCMD 设置</translation>
    </message>
    <message>
        <source>Unable to create SteamCMD runner!</source>
        <translation>无法创建 SteamCMD 运行程序！</translation>
    </message>
    <message>
        <source>There is an active process already running!</source>
        <translation>有一个活动进程已经在运行！</translation>
    </message>
    <message>
        <source>Unable to initiate SteamCMD installation. Local mods path not set!</source>
        <translation>无法启动 SteamCMD 安装。本地模组路径未设置！</translation>
    </message>
    <message>
        <source>Please configure local mods path in Settings before attempting to install.</source>
        <translation>在尝试安装之前，请在“设置”中配置本地 mods 路径。</translation>
    </message>
    <message>
        <source>SteamCMD not found</source>
        <translation>未找到 SteamCMD</translation>
    </message>
    <message>
        <source>SteamCMD executable was not found.</source>
        <translation>未找到 SteamCMD 可执行文件。</translation>
    </message>
    <message>
        <source>Please setup an existing SteamCMD prefix, or setup a new prefix with &quot;Setup SteamCMD&quot;.</source>
        <translation>请设置现有的 SteamCMD 前缀，或使用“Setup SteamCMD”设置新的前缀。</translation>
    </message>
    <message>
        <source>Processing Steam subscription action(s) via Steamworks API...</source>
        <translation>通过 Steamworks API 处理 Steam 订阅操作...</translation>
    </message>
    <message>
        <source>Download or select from local</source>
        <translation>下载或从本地选择</translation>
    </message>
    <message>
        <source>Please select a ZIP file to add to the local mods directory.</source>
        <translation>请选择一个 ZIP 文件添加到本地 mods 目录中。</translation>
    </message>
    <message>
        <source>You can download a ZIP file from the internet, or select a file from your local machine.</source>
        <translation>您可以从 Internet 下载 ZIP 文件，或从本地计算机选择文件。</translation>
    </message>
    <message>
        <source>Enter zip file url</source>
        <translation>输入 zip 文件 URL</translation>
    </message>
    <message>
        <source>Enter a zip file url (http/https) to download to local mods:</source>
        <translation>输入 zip 文件 URL (http/https) 以下载到本地 mod：</translation>
    </message>
    <message>
        <source>Failed to download zip file</source>
        <translation>下载 zip 文件失败</translation>
    </message>
    <message>
        <source>The zip file could not be downloaded.</source>
        <translation>无法下载 zip 文件。</translation>
    </message>
    <message>
        <source>File: {file_path}&lt;br&gt;Error: {e}</source>
        <translation>文件：{file_path}&lt;br&gt;错误：{e}</translation>
    </message>
    <message>
        <source>File not found</source>
        <translation>找不到文件</translation>
    </message>
    <message>
        <source>The selected file does not exist.</source>
        <translation>所选文件不存在。</translation>
    </message>
    <message>
        <source>File: {file_path}</source>
        <translation>文件： {file_path}</translation>
    </message>
    <message>
        <source>Unsupported Compression Method</source>
        <translation>不支持的压缩方法</translation>
    </message>
    <message>
        <source>This ZIP file uses a compression method that is not supported by this version.</source>
        <translation>此 ZIP 文件使用了此版本不支持的压缩方法。</translation>
    </message>
    <message>
        <source>Failed to extract zip file</source>
        <translation>无法提取 zip 文件</translation>
    </message>
    <message>
        <source>The zip file could not be extracted.</source>
        <translation>无法提取 zip 文件。</translation>
    </message>
    <message>
        <source>Existing files or directories found</source>
        <translation>找到现有文件或目录</translation>
    </message>
    <message>
        <source>All files in the archive already exist in the target path.</source>
        <translation>存档中的所有文件已存在于目标路径中。</translation>
    </message>
    <message>
        <source>How would you like to proceed?&lt;br&gt;&lt;br&gt;1) Overwrite All — Replace all existing files and directories.&lt;br&gt;2) Cancel — Abort the operation.</source>
        <translation>您想如何继续？&lt;br&gt;&lt;br&gt;1) 覆盖全部 — 替换所有现有文件和目录。&lt;br&gt;2) 取消 — 中止操作。</translation>
    </message>
    <message>
        <source>The following files or directories already exist in the target path:</source>
        <translation>目标路径中已存在以下文件或目录：</translation>
    </message>
    <message>
        <source>{conflicts_list}&lt;br&gt;&lt;br&gt;How would you like to proceed?&lt;br&gt;&lt;br&gt;1) Overwrite All — Replace all existing files and directories.&lt;br&gt;2) Skip Existing — Extract only new files and leave existing ones untouched.&lt;br&gt;3) Cancel — Abort the extraction.</source>
        <translation>{conflicts_list}&lt;br&gt;&lt;br&gt;您想如何继续？&lt;br&gt;&lt;br&gt;1) 覆盖全部 — 替换所有现有文件和目录。&lt;br&gt;2) 跳过现有 — 只提取新文件，不影响现有文件。&lt;br&gt;3) 取消 — 中止提取。</translation>
    </message>
    <message>
        <source>Extraction completed</source>
        <translation>提取完成</translation>
    </message>
    <message>
        <source>The ZIP file was successfully extracted!</source>
        <translation>ZIP 文件已成功解压！</translation>
    </message>
    <message>
        <source>Extraction failed</source>
        <translation>提取失败</translation>
    </message>
    <message>
        <source>An error occurred during extraction.</source>
        <translation>提取过程中发生错误。</translation>
    </message>
</context>
<context>
    <name>validate_rimworld_mods_list</name>
    <message>
        <source>Unable to read data</source>
        <translation>无法读取数据</translation>
    </message>
    <message>
        <source>RimDex was unable to read the supplied mods list.</source>
        <translation>RimDex 无法读取提供的模组列表。</translation>
    </message>
    <message>
        <source>The supplied mods list may be missing or invalid. If you just (re)installed RimWorld, you may need to run it once to generate the mods list.</source>
        <translation>提供的模组列表可能缺失或无效。如果你刚刚（重新）安装了 RimWorld，你可能需要运行一次以生成模组列表。</translation>
    </message>
    <message>
        <source>RimDex was unable to read the supplied mods list because it may be invalid or missing.</source>
        <translation>RimDex 无法读取提供的模组列表，因为它可能无效或缺失。</translation>
    </message>
</context>
</TS>
