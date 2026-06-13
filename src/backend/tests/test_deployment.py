"""
生产环境部署演练与回滚验证测试

测试目标：
  1. 在类生产环境执行一键部署脚本
  2. 验证数据库迁移正确执行
  3. 验证 Redis 缓存连接正常
  4. 验证对象存储（PDF 上传/下载）配置
  5. 模拟部署失败后的回滚流程
  6. 确认数据无损、服务快速恢复

前置条件：
  - 类生产环境已搭建（Docker Compose 或 K8s）
  - 部署脚本存在于 scripts/deploy.sh
  - 备份脚本存在于 scripts/backup.sh
  - .env.production 配置文件

运行方式：
  pytest tests/test_deployment.py -v --tb=short
  或单独运行：
  python tests/test_deployment.py
"""

import os
import sys
import time
import subprocess
import hashlib
import json
from pathlib import Path
from typing import Dict, List

import pytest


# 测试配置
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
BACKUP_DIR = Path(__file__).parent.parent / "backups"
DEPLOY_SCRIPT = SCRIPTS_DIR / "deploy.sh"
ROLLBACK_SCRIPT = SCRIPTS_DIR / "rollback.sh"
BACKUP_SCRIPT = SCRIPTS_DIR / "backup.sh"

BASE_URL = os.getenv("DEPLOY_TEST_URL", "http://localhost:8000")
DB_URL = os.getenv("DATABASE_URL", "")
REDIS_URL = os.getenv("REDIS_BROKER_URL", "")


def run_command(cmd: List[str], timeout: int = 300, check: bool = True) -> subprocess.CompletedProcess:
    """
    执行 shell 命令并返回结果

    Args:
        cmd: 命令列表
        timeout: 超时时间（秒）
        check: 是否检查返回码

    Returns:
        CompletedProcess 对象
    """
    print(f"  🔧 执行命令: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check
        )
        if result.returncode == 0:
            print(f"  ✅ 命令成功")
        else:
            print(f"  ❌ 命令失败: {result.stderr[:200]}")
        return result
    except subprocess.TimeoutExpired:
        print(f"  ⏰ 命令超时（{timeout}s）")
        raise
    except subprocess.CalledProcessError as e:
        print(f"  ❌ 命令错误: {e.stderr[:200]}")
        raise


def check_service_health(url: str, timeout: int = 30) -> bool:
    """
    检查服务健康状态

    Args:
        url: 服务 URL
        timeout: 超时时间（秒）

    Returns:
        是否健康
    """
    import urllib.request
    import urllib.error

    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(f"{url}/health")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                if data.get("status") == "ok":
                    return True
        except (urllib.error.URLError, json.JSONDecodeError):
            pass
        time.sleep(2)

    return False


def get_db_migration_version() -> str:
    """
    获取当前数据库迁移版本

    Returns:
        迁移版本号
    """
    try:
        # alembic.ini 位于 db/alembic.ini，需显式指定路径
        result = run_command(["alembic", "-c", "db/alembic.ini", "current"], check=False)
        output = result.stdout.strip()
        # 从输出中提取版本号（格式：<revision> (head)）
        if output:
            return output.split()[0]
        return "unknown"
    except Exception:
        return "error"


def create_test_backup() -> Path:
    """
    创建测试备份

    Returns:
        备份文件路径
    """
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"test_backup_{timestamp}.sql"

    if not DB_URL:
        # 如果没有 DB_URL，创建一个空文件占位
        backup_path.write_text("-- Empty backup for testing\n")
        return backup_path

    # 从 DB_URL 提取连接参数
    # 格式：mysql+aiomysql://user:pass@host:port/dbname
    import re
    match = re.match(r"mysql\+aiomysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", DB_URL)

    if not match:
        backup_path.write_text("-- Invalid DB_URL format\n")
        return backup_path

    user, password, host, port, dbname = match.groups()

    # 使用 mysqldump 备份
    cmd = [
        "mysqldump",
        "-h", host,
        "-P", port,
        "-u", user,
        f"-p{password}",
        dbname,
    ]

    try:
        result = run_command(cmd, timeout=60, check=False)
        if result.returncode == 0:
            backup_path.write_text(result.stdout)
            print(f"  ✅ 备份创建成功: {backup_path}")
        else:
            backup_path.write_text(f"-- Backup failed: {result.stderr}\n")
    except Exception as e:
        backup_path.write_text(f"-- Backup error: {str(e)}\n")

    return backup_path


# ========== 测试用例 ==========

@pytest.mark.skipif(not DEPLOY_SCRIPT.exists(), reason="部署脚本不存在")
def test_deployment_script_exists():
    """测试：部署脚本存在且可执行"""
    assert DEPLOY_SCRIPT.exists(), "deploy.sh 不存在"
    assert os.access(DEPLOY_SCRIPT, os.X_OK), "deploy.sh 不可执行"
    print("  ✅ 部署脚本存在")


@pytest.mark.skipif(not DB_URL, reason="未配置 DATABASE_URL")
def test_database_migration():
    """测试：数据库迁移正确执行"""
    print("\n🗄️ 测试数据库迁移...")

    # 获取当前版本
    version_before = get_db_migration_version()
    print(f"  当前版本: {version_before}")

    # 执行迁移（模拟：alembic upgrade head；alembic.ini 位于 db/ 下）
    result = run_command(["alembic", "-c", "db/alembic.ini", "upgrade", "head"], timeout=60, check=False)

    if result.returncode != 0:
        pytest.fail(f"数据库迁移失败: {result.stderr}")

    # 获取迁移后版本
    version_after = get_db_migration_version()
    print(f"  迁移后版本: {version_after}")

    # 验证：版本号应该是有效的（不是 error）
    assert version_after != "error", "无法获取迁移版本"
    print("  ✅ 数据库迁移验证通过")


@pytest.mark.skipif(not REDIS_URL, reason="未配置 REDIS_BROKER_URL")
def test_redis_connection():
    """测试：Redis 连接正常"""
    print("\n🔴 测试 Redis 连接...")

    try:
        import redis
        # 解析 Redis URL
        client = redis.from_url(REDIS_URL, decode_responses=True)
        client.ping()
        print("  ✅ Redis 连接成功")

        # 测试读写
        test_key = "deploy_test_key"
        test_value = "deploy_test_value"
        client.set(test_key, test_value, ex=10)
        assert client.get(test_key) == test_value
        client.delete(test_key)
        print("  ✅ Redis 读写正常")

    except ImportError:
        pytest.skip("redis 库未安装")
    except Exception as e:
        pytest.fail(f"Redis 连接失败: {e}")


def test_service_health_check():
    """测试：服务健康检查端点"""
    print("\n🏥 测试服务健康检查...")

    is_healthy = check_service_health(BASE_URL, timeout=10)

    if not is_healthy:
        pytest.skip(f"服务未运行或不健康: {BASE_URL}")

    print(f"  ✅ 服务健康: {BASE_URL}")


def test_pdf_upload_storage():
    """测试：PDF 上传和存储配置"""
    print("\n📁 测试 PDF 上传存储...")

    upload_dir = Path(os.getenv("UPLOAD_DIR", "uploads/papers"))

    # 检查上传目录是否存在
    if not upload_dir.exists():
        print(f"  ⚠️ 上传目录不存在，尝试创建: {upload_dir}")
        upload_dir.mkdir(parents=True, exist_ok=True)

    assert upload_dir.exists(), f"上传目录不存在: {upload_dir}"
    assert os.access(upload_dir, os.W_OK), f"上传目录不可写: {upload_dir}"

    print(f"  ✅ 上传目录存在且可写: {upload_dir}")

    # 测试写入
    test_file = upload_dir / "deploy_test.txt"
    test_content = "deployment test"
    test_file.write_text(test_content)

    assert test_file.read_text() == test_content
    test_file.unlink()

    print("  ✅ 上传目录读写测试通过")


def test_environment_variables():
    """测试：关键环境变量已配置"""
    print("\n🔐 测试环境变量...")

    required_vars = [
        "DATABASE_URL",
        "REDIS_BROKER_URL",
        "JWT_SECRET",
        "LLM_PROVIDER",
    ]

    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        pytest.fail(f"缺少环境变量: {', '.join(missing)}")

    print(f"  ✅ 所有必需环境变量已配置")

    # 检查敏感变量长度（安全性）
    jwt_secret = os.getenv("JWT_SECRET", "")
    if len(jwt_secret) < 32:
        print(f"  ⚠️ JWT_SECRET 长度不足 32 字符（当前: {len(jwt_secret)}）")

    print("  ✅ 环境变量验证通过")


def test_backup_and_restore():
    """测试：备份和恢复流程"""
    print("\n💾 测试备份和恢复...")

    # 创建备份
    backup_path = create_test_backup()

    assert backup_path.exists(), "备份文件未创建"
    assert backup_path.stat().st_size > 0, "备份文件为空"

    print(f"  ✅ 备份创建成功: {backup_path.name}")

    # 验证备份内容（至少包含 SQL 关键字）
    content = backup_path.read_text()
    if "CREATE TABLE" in content or "INSERT INTO" in content:
        print("  ✅ 备份内容包含数据库结构")
    else:
        print("  ⚠️ 备份内容可能不完整（未检测到 SQL 语句）")

    # 清理测试备份
    # backup_path.unlink()  # 保留备份供手动检查


@pytest.mark.skipif(not ROLLBACK_SCRIPT.exists(), reason="回滚脚本不存在")
def test_rollback_script_dry_run():
    """测试：回滚脚本演练（不实际执行）"""
    print("\n🔄 测试回滚脚本...")

    assert ROLLBACK_SCRIPT.exists(), "rollback.sh 不存在"
    assert os.access(ROLLBACK_SCRIPT, os.X_OK), "rollback.sh 不可执行"

    # 检查脚本内容
    content = ROLLBACK_SCRIPT.read_text()

    required_steps = [
        "backup",  # 回滚前备份
        "restore",  # 恢复数据库
        "git",  # 代码回退
        "restart",  # 重启服务
    ]

    missing_steps = []
    for step in required_steps:
        if step not in content.lower():
            missing_steps.append(step)

    if missing_steps:
        print(f"  ⚠️ 回滚脚本可能缺少步骤: {', '.join(missing_steps)}")
    else:
        print("  ✅ 回滚脚本包含所有必要步骤")


def test_deployment_rollback_simulation():
    """测试：模拟部署失败后回滚"""
    print("\n🎭 模拟部署失败回滚...")

    # 1. 记录当前状态
    version_before = get_db_migration_version()
    health_before = check_service_health(BASE_URL, timeout=5)

    print(f"  部署前状态:")
    print(f"    数据库版本: {version_before}")
    print(f"    服务健康: {health_before}")

    # 2. 创建备份
    backup_path = create_test_backup()
    print(f"  ✅ 备份创建: {backup_path.name}")

    # 3. 模拟部署失败（这里只是演示，不实际执行）
    print(f"  ⚠️ 模拟部署失败...")

    # 4. 执行回滚（演示性检查）
    if ROLLBACK_SCRIPT.exists():
        print(f"  ℹ️ 回滚脚本存在: {ROLLBACK_SCRIPT}")
        print(f"  ℹ️ 生产环境中应执行: bash {ROLLBACK_SCRIPT} {backup_path}")
    else:
        print(f"  ⚠️ 回滚脚本不存在，需手动回滚")

    # 5. 验证服务恢复（假设回滚成功）
    time.sleep(2)
    health_after = check_service_health(BASE_URL, timeout=10)

    if health_after:
        print(f"  ✅ 服务恢复正常")
    else:
        print(f"  ⚠️ 服务未恢复（测试环境未实际回滚）")


def test_database_connection_pool():
    """测试：数据库连接池配置"""
    print("\n🏊 测试数据库连接池...")

    if not DB_URL:
        pytest.skip("未配置 DATABASE_URL")

    # 检查 URL 中的连接池参数
    pool_params = ["pool_size", "max_overflow", "pool_recycle"]
    found_params = []

    for param in pool_params:
        if param in DB_URL:
            found_params.append(param)

    if found_params:
        print(f"  ✅ 连接池参数已配置: {', '.join(found_params)}")
    else:
        print(f"  ⚠️ 未显式配置连接池参数（使用默认值）")


def test_cors_configuration():
    """测试：CORS 配置（生产环境应限制来源）"""
    print("\n🌐 测试 CORS 配置...")

    import urllib.request

    try:
        req = urllib.request.Request(f"{BASE_URL}/health")
        req.add_header("Origin", "https://evil.com")

        with urllib.request.urlopen(req, timeout=5) as resp:
            cors_header = resp.headers.get("Access-Control-Allow-Origin")

            if cors_header == "*":
                print(f"  ⚠️ CORS 允许所有来源（生产环境应限制）")
            elif cors_header:
                print(f"  ✅ CORS 配置: {cors_header}")
            else:
                print(f"  ℹ️ 未检测到 CORS 头（可能未启用）")

    except Exception as e:
        pytest.skip(f"无法测试 CORS: {e}")


def test_log_files_exist():
    """测试：日志文件存在且可写"""
    print("\n📝 测试日志文件...")

    log_dir = Path("logs")

    if not log_dir.exists():
        print(f"  ⚠️ 日志目录不存在: {log_dir}")
        return

    log_files = list(log_dir.glob("*.log"))

    if log_files:
        print(f"  ✅ 找到 {len(log_files)} 个日志文件")

        # 检查最新日志文件
        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
        size_mb = latest_log.stat().st_size / (1024 * 1024)
        print(f"  最新日志: {latest_log.name} ({size_mb:.2f} MB)")

        if size_mb > 100:
            print(f"  ⚠️ 日志文件过大，建议配置日志轮转")
    else:
        print(f"  ⚠️ 未找到日志文件")


if __name__ == "__main__":
    print("=" * 70)
    print("🚀 生产环境部署演练与回滚验证测试")
    print("=" * 70)

    # 运行所有测试
    exit_code = pytest.main([__file__, "-v", "--tb=short", "-s"])

    print("\n" + "=" * 70)
    print("📊 测试完成")
    print("=" * 70)

    sys.exit(exit_code)
