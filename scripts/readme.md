# 自动化脚本目录(Example)

本目录包含用于提升开发效率和保障环境一致性的工具脚本。

## 脚本说明
- `setup_env.sh`: 一键安装开发环境所需的系统依赖。
- `data_preprocess.py`: 用于处理原始论文数据或构建索引的预处理脚本。
- `deploy.sh`: 生产环境部署脚本。

## 使用方法
sh执行脚本前请确保已授予执行权限：
```bash
chmod +x scripts/*.sh
./scripts/setup_env.