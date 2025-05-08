#!/usr/bin/env python3
import os
import sys
import subprocess
import json
import random
import string
import time

def run_command(command, shell=True):
    try:
        result = subprocess.run(command, shell=shell, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"命令执行失败: {e.stderr}"

def generate_password():
    result = subprocess.run(['openssl', 'rand', '-base64', '16'], capture_output=True, text=True)
    return result.stdout.strip()

def setup_system_parameters():
    print("正在设置系统参数...")
    commands = [
        "sysctl -w net.core.rmem_max=2500000",
        "sysctl -w net.core.wmem_max=2500000",
        "sysctl -w net.ipv4.tcp_congestion_control=bbr",
        "sysctl -w net.ipv4.tcp_fastopen=3",
        "sysctl -w net.ipv4.tcp_slow_start_after_idle=0",
        "sysctl -w net.ipv4.tcp_notsent_lowat=16384",
        "sysctl -w net.ipv4.tcp_mtu_probing=1",
        "sysctl -w net.ipv4.tcp_rmem='4096 87380 16777216'",
        "sysctl -w net.ipv4.tcp_wmem='4096 87380 16777216'",
        "sysctl -w net.core.default_qdisc=fq"
    ]
    
    # 保存系统参数到配置文件
    with open("/etc/sysctl.d/99-sysctl.conf", "w") as f:
        for cmd in commands:
            f.write(f"{cmd.split(' -w ')[1]}\n")
    
    for cmd in commands:
        success, output = run_command(cmd)
        if not success:
            print(f"警告: {cmd} 执行失败")
            continue

def setup_port_forwarding():
    print("正在设置端口转发...")
    nft_script = """#!/usr/sbin/nft -f
table ip nat {
    chain prerouting {
        type nat hook prerouting priority 0;
        policy accept;
        udp dport 20000-50000 redirect to :8443
    }
}
"""
    
    # 创建端口转发规则文件
    with open("/etc/nftables.d/port-forward.nft", "w") as f:
        f.write(nft_script)
    
    # 确保目录存在
    run_command("mkdir -p /etc/nftables.d")
    
    # 检查主配置文件是否已包含我们的规则文件
    include_line = 'include "/etc/nftables.d/port-forward.nft"'
    with open("/etc/nftables.conf", "r") as f:
        content = f.read()
    
    if include_line not in content:
        # 在文件末尾添加include语句
        with open("/etc/nftables.conf", "a") as f:
            f.write(f"\n{include_line}\n")
    
    # 启用nftables服务
    run_command("systemctl enable nftables")
    run_command("systemctl restart nftables")
    
    # 应用规则
    success, output = run_command("nft -f /etc/nftables.conf")
    if not success:
        print("警告: nft规则设置失败")
        return False
    
    return True

def install_acme():
    print("正在安装acme.sh...")
    success, output = run_command("curl https://get.acme.sh | sh")
    if not success:
        print("acme.sh安装失败")
        return False
    
    # 设置acme.sh自动更新
    run_command("acme.sh --upgrade --auto-upgrade")
    return True

def issue_certificate(domain):
    print(f"正在为域名 {domain} 申请证书...")
    # 使用DNS验证方式申请证书
    success, output = run_command(f"acme.sh --issue --dns -d {domain} --yes-I-know-dns-manual-mode-enough-go-ahead-please")
    if not success:
        print("证书申请失败")
        return False
    
    # 安装证书
    success, output = run_command(f"acme.sh --install-cert -d {domain} --key-file /root/.acme.sh/{domain}/{domain}.key --fullchain-file /root/.acme.sh/{domain}/fullchain.cer --reloadcmd 'systemctl restart sing-box'")
    if not success:
        print("证书安装失败")
        return False
    
    return True

def install_singbox():
    print("正在安装sing-box...")
    success, output = run_command("curl -fsSL https://sing-box.app/install.sh | sh")
    if not success:
        print("sing-box安装失败")
        return False
    
    # 启用sing-box服务
    run_command("systemctl enable sing-box")
    return True

def setup_singbox_config(domain, password):
    print("正在配置sing-box...")
    config = {
        "inbounds": [
            {
                "type": "shadowsocks",
                "listen": "::",
                "listen_port": 8080,
                "network": "tcp",
                "method": "2022-blake3-aes-128-gcm",
                "password": password,
                "multiplex": {
                    "enabled": True
                }
            },
            {
                "type": "hysteria2",
                "listen": "::",
                "listen_port": 8443,
                "users": [
                    {
                        "name": "xing",
                        "password": password
                    }
                ],
                "tls": {
                    "enabled": True,
                    "server_name": domain,
                    "key_path": f"/root/.acme.sh/{domain}/{domain}.key",
                    "certificate_path": f"/root/.acme.sh/{domain}/fullchain.cer"
                }
            }
        ],
        "outbounds": [
            {"type": "direct"}
        ]
    }
    
    with open("/etc/sing-box/config.json", "w") as f:
        json.dump(config, f, indent=2)

def create_client_config(domain, password):
    print("正在创建客户端配置...")
    config = {
        "outbounds": [
            {
                "type": "shadowsocks",
                "server": domain,
                "server_port": 8080,
                "method": "2022-blake3-aes-128-gcm",
                "password": password,
                "multiplex": {
                    "enabled": True
                }
            },
            {
                "type": "hysteria2",
                "server": domain,
                "server_port": 8443,
                "up_mbps": 200,
                "down_mbps": 350,
                "password": password,
                "tls": {
                    "enabled": True,
                    "server_name": domain
                }
            }
        ]
    }
    
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)

def main():
    if os.geteuid() != 0:
        print("请使用root权限运行此脚本")
        sys.exit(1)
    
    domain = input("请输入您的域名: ").strip()
    if not domain:
        print("域名不能为空")
        sys.exit(1)
    
    password = generate_password()
    
    # 执行各个步骤
    setup_system_parameters()
    if not setup_port_forwarding():
        print("端口转发设置失败")
        sys.exit(1)
    
    if not install_acme():
        print("acme.sh安装失败")
        sys.exit(1)
    
    if not issue_certificate(domain):
        print("证书申请失败")
        sys.exit(1)
    
    if not install_singbox():
        print("sing-box安装失败")
        sys.exit(1)
    
    setup_singbox_config(domain, password)
    create_client_config(domain, password)
    
    # 启动sing-box服务
    success, output = run_command("systemctl restart sing-box")
    if not success:
        print("sing-box服务启动失败")
        sys.exit(1)
    
    # 检查服务状态
    success, output = run_command("systemctl status sing-box")
    if not success:
        print("sing-box服务状态异常")
        run_command("systemctl stop sing-box")
        sys.exit(1)
    
    print("\n=== 配置完成 ===")
    print(f"域名: {domain}")
    print(f"密码: {password}")
    print(f"Shadowsocks端口: 8080")
    print(f"Hysteria2端口: 8443")
    print("\n客户端配置文件已保存为当前目录下的config.json")
    print("\n请确保您的域名已正确解析到服务器IP")
    print("如果使用DNS验证方式申请证书，请按照提示设置DNS记录")

if __name__ == "__main__":
    main() 