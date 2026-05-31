# 汉献帝之末路 - UI升级方案

## 已完成工作

### 1. 头像系统
- **MinisterPortrait.tsx**: 三级fallback头像组件（专属立绘 → 池头像 → 占位符）
- **MinisterPortrait.css**: 完整的头像样式系统
- **头像资源**: 从ming-salvage-sim复制的80+人物头像
- 支持自定义上传立绘功能

### 2. 朝会布局系统
- **CourtLayout.tsx**: 双模式朝会视图
  - 网格模式：传统列表展示
  - 透视模式：3D透视布局，大臣可拖拽定位
- **CourtLayout.css**: 朝会场景样式，含透视地板、皇帝御座、大臣卡片

### 3. 派系关系图
- **FactionRelationDiagram.tsx**: SVG派系关系可视化
  - 圆形布局，中心为天子
  - 同盟/对立/中立关系线
  - 影响力进度环
  - 悬停高亮交互

### 4. 动画系统
- 已有animations.css含30+古风动画
- 新增朝会专用动画（皇帝御座光晕、大臣卡片悬浮等）

### 5. 打包配置
- **HanEmpireSim.spec**: 完整PyInstaller配置
- 支持Windows exe桌面应用
- 包含所有资源文件和动态模块

## 待完成工作

### 1. 地图与省份视图
- 需实现ProvinceMap组件（汉末十三州）
- 参考ming-salvage-sim的GrandMap实现
- SVG或Canvas渲染地图

### 2. App.tsx集成
- 将新组件集成到主应用
- 朝会视图Tab切换
- 派系关系图Tab

### 3. 人物立绘
- 当前使用ming-salvage-sim的头像（明朝风格）
- 需要替换为汉末风格人物立绘
- 可使用AI生成或手动绘制

### 4. 场景插画
- 洛阳/许昌宫殿背景
- 董卓/曹操等势力标志
-诏书/圣旨等UI元素图

## 技术架构

```
han-empire/
├── web/src/
│   ├── components/
│   │   ├── MinisterPortrait.tsx  ✓
│   │   ├── MinisterPortrait.css  ✓
│   │   ├── CourtLayout.tsx       ✓
│   │   ├── CourtLayout.css       ✓
│   │   ├── FactionRelationDiagram.tsx  ✓
│   │   └── FactionRelationDiagram.css ✓
│   ├── styles/
│   │   ├── app.css
│   │   └── animations.css
│   └── App.tsx
├── web/public/
│   ├── portraits/         (80+头像)
│   ├── images/
│   └── animations/
├── HanEmpireSim.spec      ✓
└── launcher.py
```

## Windows桌面打包流程

```bash
cd C:\Users\lz\han-empire

# 安装依赖
pip install -e .

# 打包exe
pyinstaller HanEmpireSim.spec

# 产物位置
dist/HanEmpireSim/HanEmpireSim.exe
```

## 前端开发

```bash
cd C:\Users\lz\han-empire\web

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build
```