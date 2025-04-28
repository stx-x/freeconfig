# sing-box 服务器及客户端搭建完全指南

## 服务器端
### 参考：[官方安装指南](https://sing-box.sagernet.org/installation/package-manager/#repository-installation)
1. 安装 sing-box 服务
   `curl -fsSL https://sing-box.app/install.sh | sh`
2. 编辑配置文件
   
  - 将本文件夹下 `server-config.json` 复制到 `/etc/sing-box/config`
- 编辑该文件，修改5处，
- 密码生成可以采用命令 `openssl rand -base64 16`
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
