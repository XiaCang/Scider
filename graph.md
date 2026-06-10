# Scider 前端项目架构流程图

## 1. 当前架构（重构前）

```mermaid
graph TD
    A[Vue 组件] --> B[直接在组件中]
    B --> C[API 调用]
    B --> D[业务逻辑]
    B --> E[状态管理]
    B --> F[UI 渲染]
    
    C --> G[网络请求层]
    D --> H[混合在组件中]
    E --> I[分散的状态]
    F --> J[模板和样式]
    
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style H fill:#f96,stroke:#333,stroke-width:2px
```

## 2. 目标架构（重构后）

```mermaid
graph TD
    subgraph "用户界面层 (UI Layer)"
        A1[页面组件 Page Views]
        A2[业务组件 Business Components]
        A3[通用组件 Shared Components]
    end
    
    subgraph "逻辑层 (Logic Layer)"
        B1[Composition Functions]
        B2[自定义 Hooks]
        B3[服务层 Services]
    end
    
    subgraph "状态管理层 (State Layer)"
        C1[Pinia Store - Library]
        C2[Pinia Store - Auth]
        C3[Pinia Store - Dashboard]
    end
    
    subgraph "数据访问层 (Data Layer)"
        D1[API 接口定义]
        D2[HTTP 客户端]
        D3[数据验证]
    end
    
    subgraph "基础设施层 (Infrastructure Layer)"
        E1[类型定义 Types]
        E2[工具函数 Utils]
        E3[常量配置 Constants]
    end
    
    A1 --> B1
    A2 --> B2
    B1 --> C1
    B2 --> C2
    B3 --> D1
    C1 --> D1
    C2 --> D1
    C3 --> D1
    D1 --> D2
    D2 --> E1
    
    style A1 fill:#e1f5fe,stroke:#01579b
    style A2 fill:#e1f5fe,stroke:#01579b
    style A3 fill:#e1f5fe,stroke:#01579b
    style B1 fill:#f3e5f5,stroke:#4a148c
    style B2 fill:#f3e5f5,stroke:#4a148c
    style B3 fill:#f3e5f5,stroke:#4a148c
    style C1 fill:#e8f5e8,stroke:#1b5e20
    style C2 fill:#e8f5e8,stroke:#1b5e20
    style C3 fill:#e8f5e8,stroke:#1b5e20
    style D1 fill:#fff3e0,stroke:#e65100
    style D2 fill:#fff3e0,stroke:#e65100
    style D3 fill:#fff3e0,stroke:#e65100
    style E1 fill:#fce4ec,stroke:#880e4f
    style E2 fill:#fce4ec,stroke:#880e4f
    style E3 fill:#fce4ec,stroke:#880e4f
```

## 3. 模块化组织结构

```mermaid
graph TD
    subgraph "根目录结构"
        src[src/]
    end
    
    src --> modules
    src --> shared
    src --> views
    src --> router[router/]
    src --> store[store/]
    
    subgraph "shared/ (共享层)"
        shared --> shared_components[components/]
        shared --> shared_composables[composables/]
        shared --> shared_utils[utils/]
        shared --> shared_types[types/]
    end
    
    subgraph "modules/ (功能模块)"
        modules --> library
        modules --> auth
        modules --> dashboard
        modules --> graph
        modules --> discover
    end
    
    subgraph "library/ (论文库模块)"
        library --> lib_components[components/]
        library --> lib_composables[composables/]
        library --> lib_services[services/]
        library --> lib_types[types/]
        library --> lib_views[views/]
        library --> lib_index[index.ts]
    end
    
    subgraph "auth/ (认证模块)"
        auth --> auth_components[components/]
        auth --> auth_composables[composables/]
        auth --> auth_services[services/]
        auth --> auth_index[index.ts]
    end
    
    shared_composables --> shared_hooks[通用 Hooks]
    shared_components --> ui_components[UI 组件]
    
    lib_composables --> useLibraryManagement
    lib_services --> LibraryService
    lib_components --> FolderTree
    lib_components --> PaperList
    
    style src fill:#bbdefb,stroke:#0d47a1,stroke-width:3px
    style modules fill:#c8e6c9,stroke:#1b5e20
    style shared fill:#fff9c4,stroke:#f57f17
    style library fill:#e1bee7,stroke:#4a148c
    style auth fill:#ffccbc,stroke:#bf360c
```

## 4. 数据流架构

```mermaid
sequenceDiagram
    participant U as 用户界面
    participant C as Composition Function
    participant S as Store (Pinia)
    participant SV as Service 层
    participant API as API 接口
    participant BE as 后端服务
    
    U->>C: 触发动作 (如搜索)
    C->>S: 调用 Action
    S->>SV: 委托给 Service
    SV->>API: 调用 API 方法
    API->>BE: 发送 HTTP 请求
    BE-->>API: 返回响应
    API-->>SV: 返回数据
    SV-->>S: 更新 State
    S-->>C: 返回最新状态
    C-->>U: 触发响应式更新
    U->>U: 重新渲染 UI
```

## 5. 组件通信模式

```mermaid
graph LR
    subgraph "组件间通信模式"
        A[父组件 Parent] -->|Props 传递| B[子组件 Child]
        B -->|Emit 事件| A
        
        C[组件 A] -->|Provide| D[Context]
        D -->|Inject| E[组件 B]
        
        F[任意组件] -->|Store Getter| G[Pinia Store]
        G -->|Store Action| H[任意组件]
        
        I[组件] -->|调用| J[Composition Function]
        J -->|返回响应式数据| I
        
        K[组件] -->|使用| L[自定义 Hook]
        L -->|封装复杂逻辑| K
    end
    
    style A fill:#e1f5fe,stroke:#01579b
    style B fill:#e1f5fe,stroke:#01579b
    style C fill:#f1f8e9,stroke:#33691e
    style E fill:#f1f8e9,stroke:#33691e
    style F fill:#fff8e1,stroke:#ff6f00
    style H fill:#fff8e1,stroke:#ff6f00
    style I fill:#fce4ec,stroke:#880e4f
    style K fill:#e8eaf6,stroke:#283593
```

## 6. 文件职责分离示意图

```mermaid
graph TB
    subgraph "Vue 组件文件 (重构后)"
        V[Vue 组件] --> VS[script setup 部分]
        V --> VT[template 部分]
        V --> VC[style 部分]
        
        VS --> VST[TypeScript 类型定义]
        VS --> VSI[导入 Composition Functions]
        VS --> VSR[响应式变量声明]
        
        VT --> VTD[模板语法]
        VT --> VTC[组件使用]
        VT --> VTE[事件绑定]
        
        VC --> VCS[Scoped 样式]
        VC --> VCV[CSS 变量使用]
    end
    
    subgraph "独立的 TS 文件"
        TS[TypeScript 文件] --> TSF[Composition Functions]
        TS --> TSH[自定义 Hooks]
        TS --> TSS[Services]
        TS --> TST[类型定义]
        TS --> TSU[工具函数]
        
        TSF --> TSFL[业务逻辑实现]
        TSF --> TSFE[响应式变量]
        TSF --> TSFX[导出函数]
    end
    
    VSI -.-> TSF
    VST -.-> TST
    
    style V fill:#e3f2fd,stroke:#1565c0
    style TS fill:#f3e5f5,stroke:#7b1fa2
    style TSF fill:#c8e6c9,stroke:#2e7d32
    style TST fill:#bbdefb,stroke:#0d47a1
```

## 7. 状态管理流程图

```mermaid
stateDiagram-v2
    [*] --> 组件加载
    
    组件加载 --> 调用StoreAction: 用户交互
    调用StoreAction --> 调用Service: 委托业务逻辑
    
    state 调用Service {
        [*] --> 参数验证
        参数验证 --> API调用: 验证通过
        参数验证 --> 错误处理: 验证失败
        API调用 --> 数据处理: 成功响应
        API调用 --> 错误处理: API错误
        数据处理 --> 更新Store: 处理完成
        错误处理 --> 返回错误: 错误处理完成
    }
    
    调用Service --> 更新Store: Service返回数据
    更新Store --> 触发响应: State变更
    触发响应 --> 组件更新: 重新计算Computed
    组件更新 --> [*]: 渲染完成
```

## 8. API 调用链

```mermaid
graph TD
    C[组件 Component] --> CF[Composition Function]
    CF --> S[Store Action]
    S --> SV[Service 层]
    SV --> API[API Interface]
    API --> HTTP[HTTP Client]
    HTTP --> BE[Backend API]
    
    BE --响应--> HTTP
    HTTP --数据--> API
    API --转换--> SV
    SV --更新--> S
    S --状态变更--> CF
    CF --响应式更新--> C
    
    subgraph "错误处理链"
        HTTP --错误--> EH[错误处理]
        EH --> S
    
        API --验证错误--> EV[数据验证]
        EV --> CF
        
        SV --业务错误--> BEH[业务错误处理]
        BEH --> S
    end
    
    style C fill:#e1f5fe,stroke:#01579b
    style CF fill:#f3e5f5,stroke:#4a148c
    style S fill:#e8f5e8,stroke:#1b5e20
    style SV fill:#fff3e0,stroke:#e65100
    style API fill:#fce4ec,stroke:#880e4f
```

## 9. 开发工作流程

```mermaid
flowchart TD
    START[开始开发] --> STEP1[分析需求]
    STEP1 --> STEP2[设计类型接口<br/>src/types/]
    
    subgraph "前端实现"
        STEP2 --> STEP3[创建 Composition Function<br/>src/composables/]
        STEP3 --> STEP4[创建 Service<br/>src/services/]
        STEP4 --> STEP5[实现 Store<br/>src/store/]
        STEP5 --> STEP6[创建组件<br/>src/components/]
        STEP6 --> STEP7[创建页面<br/>src/views/]
        STEP7 --> STEP8[配置路由<br/>src/router/]
    end
    
    STEP8 --> STEP9[编写单元测试<br/>tests/]
    STEP9 --> STEP10[集成测试]
    STEP10 --> END[完成]
    
    style START fill:#c8e6c9,stroke:#1b5e20,stroke-width:2px
    style END fill:#ffccbc,stroke:#bf360c,stroke-width:2px
    style STEP2 fill:#bbdefb,stroke:#0d47a1
    style STEP3 fill:#e1bee7,stroke:#4a148c
    style STEP4 fill:#fff9c4,stroke:#f57f17
    style STEP6 fill:#d1c4e9,stroke:#311b92
```

## 10. 总结：架构优势对比

```mermaid
graph LR
    subgraph "重构前: 混合模式"
        A1[大而全的 Vue 文件]
        A1 --> A2[高耦合度]
        A1 --> A3[难测试]
        A1 --> A4[低复用性]
        A1 --> A5[维护困难]
    end
    
    subgraph "重构后: 分层架构"
        B1[清晰的职责分离]
        B1 --> B2[低耦合]
        B1 --> B3[易测试]
        B1 --> B4[高复用]
        B1 --> B5[易维护]
    end
    
    A1 -- 重构 --> B1
    
    style A1 fill:#ffcdd2,stroke:#b71c1c
    style B1 fill:#c8e6c9,stroke:#1b5e20
```

---

## 架构核心原则

1. **单一职责原则**: 每个文件/类/函数只负责一件事
2. **依赖倒置原则**: 高层模块不依赖低层模块，都依赖抽象
3. **开闭原则**: 对扩展开放，对修改关闭
4. **关注点分离**: UI、逻辑、数据、状态各司其职
5. **最小知识原则**: 组件只了解必要的依赖

## 技术决策依据

1. **使用 Composition API**: 更好的逻辑复用和代码组织
2. **模块化架构**: 按功能划分，提高内聚降低耦合
3. **TypeScript 优先**: 类型安全，更好的开发体验
4. **Pinia 状态管理**: Vue 3 官方推荐，TypeScript 友好
5. **Service 层抽象**: 分离业务逻辑和 UI 逻辑

这个架构设计支持项目的长期演进，能够随着功能增加而扩展，同时保持代码的可维护性和可测试性。