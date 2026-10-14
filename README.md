# ZIP 兼容工具｜UTF-8 与内容校验

根据公开 ZIP 接口独立实现的跨平台小工具，修复缺失 UTF-8 标志造成的文件名误读，清理 macOS 元数据并验证内容字节。

> 公开方法演示 / Public methodology demo。合成数据不代表原项目成果，具体实现由 AI 编程工具辅助完成。

## 功能

- 仅当未设 UTF-8 flag 且原字节可解码为 UTF-8 时修复；不猜测 GBK。
- 保留文件逐个做 SHA-256 验证；不提取 ZIP 到文件系统。
- 拒绝覆盖、目录穿越、大小写重名、加密包及符号链接。
- 随机临时文件与同文件系统硬链接发布，失败清理本次临时产物。

## 本地运行

Python 3.11+。

```sh
python -m pip install -r requirements.txt
python demo.py
python -m unittest discover -s tests -v
```

入口：`repair_zip.py`。不需要 API Key、数据库、网络服务或付费模型。

处理自己的 ZIP（生成新文件）：

```sh
python repair_zip.py example.zip --output repaired.zip
```

## 流程

```mermaid
flowchart LR
A[输入 ZIP] --> B[路径/重名/限额检查]
  B --> C[文件名修复与元数据过滤]
  C --> D[临时重建]
  D --> E[逐文件 SHA-256]
  E --> F[拒绝覆盖的发布]
```

## 验证

本地验证记录见 [VERIFICATION.md](VERIFICATION.md)。GitHub Actions 在 push 与 PR 时运行相同的离线测试；本地通过不代表远端 CI 已通过。

## 数据与局限

最多 10,000 个成员、512MiB 声明未压缩体积。需支持硬链接的输出文件系统（Windows NTFS、常规 Linux 文件系统）；不支持 FAT/某些网络盘，失败不会覆盖旧文件。压缩参数与 ZIP 元数据可能改变，只保证保留文件内容经过字节比对。不是原实习 PowerShell 文件的公开副本。

测试压缩包在临时目录动态生成，只有合成内容；不包含公司文档或业务附件。

## 许可与贡献

独立公开实现代码：MIT。合成样例随仓库发布，不向使用者授予任何第三方商业数据权利。没有捆绑原公司或团队源码。依赖与公开接口归因见 [NOTICE](NOTICE)。

[作品集](https://github.com/Willow-Tokoton-Hitorineko/research-portfolio) · [个人主页](https://github.com/Willow-Tokoton-Hitorineko)
