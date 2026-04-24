
## 修改
如有修改，再这里说明

## 环境准备
1. 创建并启动 MySQL 数据库（示例库名 `db`）。
2. 进入到db目录下，安装依赖（位于 `backend/db/`）：
```
python -m pip install -r requirements.txt
```

3. 设置数据库连接,设置环境变量：
```
# 示例 DATABASE_URL（asyncmy 驱动）
$env:DATABASE_URL = "mysql+asyncmy://dbuser:dbpass@dbhost:3306/dbname?charset=utf8mb4"
# 可选连接池配置
$env:DB_POOL_SIZE = "5"
$env:DB_MAX_OVERFLOW = "10"
$env:DB_POOL_RECYCLE = "3600"
```
4. 运行 Alembic 迁移（请确保 `DATABASE_URL` 已指向存在的数据库）：
```
# 使用位于 `db/alembic.ini` 的配置运行 Alembic：
alembic -c alembic.ini upgrade head
```

运行示例

- 运行 CRUD demo（会创建/查询/更新/删除测试用户）
```
python -m db_test.demo_user_crud
```

- 运行连接池并发测试（观察 pool.status() 输出）
```
python -m db_test.pool_test
```





### user
```
op.create_table(
    'user',
    sa.Column('id', sa.String(64), primary_key=True),
    //id作为主键
    sa.Column('email', sa.String(255), nullable=False, unique=True),
    //邮箱：唯一且非空
    sa.Column('password', sa.String(255), nullable=False),
    //密码：非空
    sa.Column('name', sa.String(255)),
    //用户名
    sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    //创建时间：非空，由数据库自动填写
    sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    //更新时间：非空，由数据库自动发填写
)
```

### Folder 表
```
op.create_table(
    'folder',
    sa.Column('id', sa.String(64), primary_key=True),  # id主键
    sa.Column('name', sa.String(255), nullable=False),  # 文件夹名，非空
    sa.Column('user_id', sa.String(64), sa.ForeignKey('user.id'), nullable=False), 
     # 所属用户，非空，外键关联user表
    sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False), 
     # 创建时间，非空，数据库自动填写
)
```

### Paper 表
```
op.create_table(
    'paper',
    sa.Column('id', sa.String(64), primary_key=True),
    sa.Column('title', sa.String(1024), nullable=False),  # 标题：非空
    sa.Column('authors', sa.Text(), nullable=True),  # 作者列表（JSON/text）
    sa.Column('abstract', sa.Text(), nullable=True),  # 摘要
    sa.Column('doi', sa.String(255), nullable=True, unique=True),  # DOI：唯一，可空
    sa.Column('year', sa.Integer(), nullable=True),  # 年份
    sa.Column('pdf_path', sa.String(1024), nullable=True),  # PDF 路径
    sa.Column('user_id', sa.String(64), sa.ForeignKey('user.id'), nullable=False),  # 上传用户
    sa.Column('folder_id', sa.String(64), sa.ForeignKey('folder.id'), nullable=True),  # 所属文件夹
    sa.Column(
        'status',
        sa.Enum(
            'PENDING_PARSING', 'PARSING', 'PENDING_EXTRACTION', 'EXTRACTING',
            'PENDING_CONFIRMATION', 'CONFIRMED', 'FAILED',
            name='paperstatus'
        ),
        nullable=False,
        server_default=sa.text("'PENDING_PARSING'")  # 默认状态
    ),
    sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
)
```

### KeyPoints 表（每篇 paper 对应一条 keypoints）
```
op.create_table(
    'keypoints',
    sa.Column('id', sa.String(64), primary_key=True),
    sa.Column('paper_id', sa.String(64), sa.ForeignKey('paper.id'), unique=True, nullable=False),  # 一对一
    sa.Column('background', sa.Text(), nullable=True),
    sa.Column('methodology', sa.Text(), nullable=True),
    sa.Column('innovation', sa.Text(), nullable=True),
    sa.Column('conclusion', sa.Text(), nullable=True),
    sa.Column('is_confirmed', sa.Boolean(), nullable=False, server_default=sa.text("0")),  # 布尔默认 0
    sa.Column('confirmed_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
)
```
### Tag 表
```
op.create_table(
    'tag',
    sa.Column('id', sa.String(64), primary_key=True),
    sa.Column('name', sa.String(255), nullable=False),  # 标签名
)
```

### 关联表 paper_tag (paper与tag多对多关系)
```
op.create_table(
    'paper_tag',
    sa.Column('paper_id', sa.String(64), sa.ForeignKey('paper.id'), primary_key=True),
    sa.Column('tag_id', sa.String(64), sa.ForeignKey('tag.id'), primary_key=True),
)
```

### Task 表（后台任务队列）
```
op.create_table(
    'task',
    sa.Column('id', sa.String(64), primary_key=True),
    sa.Column(
        'type',
        sa.Enum('PDF_PARSE', 'LLM_EXTRACT', name='tasktype'),
        nullable=False
    ),  # 任务类型
    sa.Column(
        'status',
        sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='taskstatus'),
        nullable=False,
        server_default=sa.text("'PENDING'")
    ),  # 任务状态
    sa.Column('paper_id', sa.String(64), sa.ForeignKey('paper.id'), nullable=True),
    sa.Column('progress', sa.Integer(), nullable=False, server_default="0"),
    sa.Column('result', sa.JSON(), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
)
```