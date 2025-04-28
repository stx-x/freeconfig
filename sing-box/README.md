# sing-box 服务器及客户端搭建完全指南

## 服务器端
### 参考：[官方安装指南](https://sing-box.sagernet.org/installation/package-manager/#repository-installation)
1. 安装 sing-box 服务
   `curl -fsSL https://sing-box.app/install.sh | sh`
2. 编辑配置文件
   
  - 将本文件夹下 `server-config.json` 复制到 `/etc/sing-box/config`
- 编辑该文件，修改5处，
- 密码生成可以采用命令 `openssl rand -base64 16`
- cloudflare tokens 的获取参见下文。
> 可以用命令 `sing-box check -c /etc/sing-box/config` 检查是否有错误
> 
> 可以用命令 `sing-box format -w -c /etc/sing-box/config` 进行格式化
3. 启用sing-box daemon服务（马上运行并且重启后会自动启动）
   `sudo systemctl enable --now sing-box`
4. 查看状态和实时日志
   `sudo systemctl status sing-box`
   `sudo journalctl -u sing-box --output cat -f`
- 如果 显示 sing-box  `enabled` 和 `activing` 两个绿色，并且日志显示sing-box正常监听，说明没问题了，正常运行。
- 很有可能acme token那边会出问题，这个时候先停止sing-box，用命令`sudo systemctl stop sing-box`，不然会一直用错误的token重试。重新弄个token后再试。
- 其他常用命令可参考[官方安装指南](https://sing-box.sagernet.org/installation/package-manager/#repository-installation)

## 客户端
修改客户端配置文件的 密码和域名部分，注意密码需要和相应服务器端一致。比如 `ss`协议的服务器和客户端要一致，`hy2`协议的服务器和客户端要一致。但是这两个协议可以不一致。
- `ss`协议一个密码一个域名要改，`hy2`两个域名（两个地方填同一个域名）一个协议要改。
- 根据需要修改其他部分
- 默认用`自动测速`，线路好建议用`ss`，线路不好用`hy2`

## Cloudflare 平台生成一个专门为 ACME 协议客户端设计的 API 令牌（Token）
> 以下为AI生成：
1.  **登录 Cloudflare 控制面板:**
    *   请访问 Cloudflare 官方网站 `https://dash.cloudflare.com`。
    *   使用您的账户凭据（电子邮箱地址和密码）完成身份验证并登录。

2.  **导航至 API 令牌管理界面:**
    *   登录成功后，请将鼠标悬停于控制面板右上角的用户图标或用户名处。
    *   在弹出的下拉菜单中，选择“**我的个人资料** (My Profile)”。
    *   在“我的个人资料”页面，请关注左侧导航菜单，并点击“**API 令牌** (API Tokens)”选项卡。

3.  **启动令牌创建流程:**
    *   在“API 令牌”管理页面，点击显著的“**创建令牌** (Create Token)”按钮。

4.  **选择令牌模板类型:**
    *   Cloudflare 提供多种令牌模板。为实现精确的权限控制，请在“自定义令牌 (Custom token)”区域，点击“**开始使用** (Get started)”按钮。

5.  **令牌属性配置 - 命名:**
    *   在“**令牌名称** (Token name)”字段中，输入一个具有描述性的名称，以便于未来识别此令牌的用途。推荐采用明确的命名规范，例如：“`ACME_DNS01_Token_yourdomain.com`”。

6.  **令牌属性配置 - 权限 (Permissions):**
    *   此为关键配置步骤，请审慎操作。
    *   点击“**添加权限** (Add Permission)”或在权限配置区域进行设置。
    *   **权限集一：**
        *   选择权限类别：**区域 (Zone)**
        *   选择资源类型：**DNS**
        *   选择权限级别：**编辑 (Edit)**
    *   *说明：* 此权限组合允许 ACME 客户端读取、创建和删除指定区域（域名）的 DNS 记录，这是执行 DNS-01 验证（通过添加和移除 TXT 记录）所必需的操作。仅授予“编辑”权限已足够，无需“读取”之外的更高级别权限。

7.  **令牌属性配置 - 区域资源 (Zone Resources):**
    *   此步骤限定该令牌可操作的域名范围，对于安全性至关重要。
    *   **强烈建议**避免选择“所有区域 (All zones)”。
    *   选择包含关系：“**包含 (Include)**”
    *   选择资源类型：“**特定区域 (Specific zone)**”
    *   在下方的选择框中，精确指定您计划使用 ACME 自动管理证书的一个或多个域名（例如 `example.com`）。仅授权给必要的域名，以符合最小权限原则。

8.  **令牌属性配置 - （可选）客户端 IP 地址筛选 (Client IP Address Filtering):**
    *   若您的 ACME 客户端运行在具有固定公网 IP 地址的服务器上，可在此处配置允许访问的源 IP 地址或 CIDR 范围，以增强安全性。
    *   如果客户端 IP 不固定或存在网络地址转换 (NAT)，请将此项留空。

9.  **令牌属性配置 - （可选）生存时间 (TTL):**
    *   您可以设定令牌的有效期限。默认设置为“无结束日期 (No End Date)”，即永久有效。根据您的安全策略，可选择设定一个具体的失效日期。对于 ACME 自动化场景，通常保持默认设置。

10. **预览与确认:**
    *   完成上述配置后，滚动至页面底部，点击“**继续以显示摘要** (Continue to summary)”。
    *   请仔细核对摘要页面显示的令牌名称、权限配置及作用域资源，确保所有设置均符合预期。

11. **生成并安全存储令牌:**
    *   确认无误后，点击“**创建令牌** (Create Token)”按钮。
    *   系统将生成 API 令牌，并**仅在此页面显示一次**。
    *   **请务必立即复制生成的令牌字符串。** 这是一串敏感凭证。
    *   **强烈建议**将此令牌妥善存储在安全的密码管理器或加密存储介质中。**切勿**将其明文硬编码于代码、配置文件中，或通过不安全的渠道传输。一旦泄露，可能导致您的 DNS 记录被未授权修改。
