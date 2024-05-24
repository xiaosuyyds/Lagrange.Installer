# Lagrange.Installer
> #### 一个针对 [Lagrange.OneBot](https://github.com/LagrangeDev/Lagrange.Core) 的安装脚本

## 💻如何安装

1. 下载最新的 [releases](https://github.com/xiaosuyyds/Lagrange.Installer/releases)
2. 运行 `Installer`
3. 等待安装完成

## 📖使用说明

1. 支持启动参数，运行命令:`Installer -h`即可查看
2. 默认安装在 `./OneBot`

## 💭常见问题

1. 下载失败: 有可能是访问次数过多，被github.com限制，过段时间再试，或是开启代理等方法

## 📋TODO List

- [x] 辅助首次登录流程
- [x] 多线程下载
- [x] 静默安装（无法运行辅助首次登录流程）
- [x] 添加自定义启动参数（是否开启代理、代理端口等）
- [x] 添加自定义安装路径（默认安装在 `./OneBot`）
- [ ] 添加自动更新功能（不删除配置文件，仅更新Lagrange.OneBot）
- [ ] 添加shell版本的安装脚本
- [ ] 安装actions而非releases内的Lagrange.OneBot
