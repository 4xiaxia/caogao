# 🎨 Naive UI 马卡龙主题配置

**配置日期:** 2026-03-01  
**主题风格:** baby 嘭嘭软软 · 微膨胀培乐多  
**框架:** Naive UI (Vue 3)

---

## 📦 第一步：安装 Naive UI

```bash
cd console

# 安装 Naive UI
npm install naive-ui

# 安装图标库
npm install @vicons/ionicons5
```

---

## 🎨 第二步：创建马卡龙主题

**文件:** `console/theme/macaronTheme.js`

```javascript
import { createTheme, lightTheme } from 'naive-ui'

// 马卡龙色系
const macaronColors = {
  // 主色 - 马卡龙紫
  primary: '#B19CD9',
  primaryHover: '#C7B5E0',
  primaryPressed: '#9A82C4',
  
  // 辅助色
  success: '#BCE6C9',      // 马卡龙绿
  warning: '#FFF5BA',      // 马卡龙黄
  error: '#FFB7C5',        // 马卡龙粉
  info: '#AECBEB',         // 马卡龙蓝
  
  // 中性色
  baseColor: '#FDFBF0',    // 奶油白
  textColor: '#584840',    // 深棕
  borderColor: '#E8D8B8',  // 米色
}

// 马卡龙主题配置
export const macaronTheme = createTheme({
  common: {
    // 主色
    primaryColor: macaronColors.primary,
    primaryColorHover: macaronColors.primaryHover,
    primaryColorPressed: macaronColors.primaryPressed,
    primaryColorSuppl: macaronColors.primaryHover,
    
    // 成功色
    successColor: macaronColors.success,
    successColorHover: '#D0F0DA',
    successColorPressed: '#A5D9B8',
    
    // 警告色
    warningColor: macaronColors.warning,
    warningColorHover: '#FFF9D0',
    warningColorPressed: '#FFEBA5',
    
    // 错误色
    errorColor: macaronColors.error,
    errorColorHover: '#FFC9D5',
    errorColorPressed: '#FFA5B8',
    
    // 信息色
    infoColor: macaronColors.info,
    infoColorHover: '#C5D8F0',
    infoColorPressed: '#95B8E0',
    
    // 背景色
    bodyColor: macaronColors.baseColor,
    cardColor: '#FFF9F0',
    modalColor: '#FFF9F0',
    popoverColor: '#FFF5E8',
    
    // 文字颜色
    textColorBase: macaronColors.textColor,
    textColor1: '#3A3028',
    textColor2: '#584840',
    textColor3: '#786858',
    
    // 边框颜色
    borderColor: macaronColors.borderColor,
    dividerColor: '#F2EBD4',
    
    // baby 嘭嘭圆角
    borderRadius: '20px',
    borderRadiusSmall: '12px',
    borderRadiusMedium: '16px',
    borderRadiusLarge: '24px',
    
    // 柔软阴影 - 微膨胀效果
    boxShadow1: '0 2px 8px rgba(177, 156, 217, 0.1)',
    boxShadow2: '0 4px 16px rgba(177, 156, 217, 0.15)',
    boxShadow3: '0 8px 24px rgba(177, 156, 217, 0.2)',
    
    // 聚焦效果
    focusColor: macaronColors.primary,
    focusBoxShadow: '0 0 0 3px rgba(177, 156, 217, 0.15)',
    
    // 禁用效果
    disabledColor: '#E8D8B8',
    disabledTextColor: '#B8A888',
  },
  
  // Button 组件定制 - 培乐多质感
  Button: {
    borderRadius: '24px',
    borderRadiusSmall: '16px',
    fontWeight: '600',
    fontSizeTiny: '13px',
    fontSizeSmall: '14px',
    fontSizeMedium: '15px',
    fontSizeLarge: '16px',
    
    // 按压效果 - 嘭嘭感
    pressedOpacity: '0.9',
  },
  
  // Card 组件定制 - 圆润饱满
  Card: {
    borderRadius: '20px',
    borderColor: 'rgba(177, 156, 217, 0.15)',
    boxShadow: '0 8px 24px rgba(177, 156, 217, 0.15)',
    
    // 微膨胀背景
    colorEmbedded: 'linear-gradient(135deg, #FFF9F0 0%, #FFF5E8 100%)',
  },
  
  // Input 组件定制 - 柔和
  Input: {
    borderRadius: '16px',
    border: '2px solid #E8D8B8',
    borderHover: '2px solid #B19CD9',
    borderFocus: '2px solid #B19CD9',
    
    // 内阴影
    boxShadowFocus: '0 0 0 3px rgba(177, 156, 217, 0.1)',
  },
  
  // Tag 组件定制 - 小圆角
  Tag: {
    borderRadius: '12px',
    fontSize: '13px',
    fontWeight: '600',
  },
  
  // Space 组件 - 间距柔和
  Space: {
    gapTiny: '8px',
    gapSmall: '12px',
    gapMedium: '16px',
    gapLarge: '24px',
  },
})

// 导出基础浅色主题（作为基底）
export { lightTheme }
```

---

## 🏗️ 第三步：在 App 中应用主题

**文件:** `console/App.vue`

```vue
<template>
  <n-config-provider :theme="macaronTheme">
    <n-global-style />
    <n-message-provider>
      <n-dialog-provider>
        <router-view />
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { NConfigProvider, NGlobalStyle, NMessageProvider, NDialogProvider } from 'naive-ui'
import { macaronTheme } from './theme/macaronTheme'
</script>

<style>
/* 全局样式 - 马卡龙基底 */
body {
  background: linear-gradient(135deg, #FDFBF0 0%, #F9F6E8 100%);
  color: #584840;
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* 滚动条美化 - 马卡龙紫 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #F2EBD4;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #B19CD9;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #C7B5E0;
}
</style>
```

---

## 🎨 第四步：创建示例页面

**文件:** `console/pages/Home.vue`

```vue
<template>
  <div class="home-page">
    <n-space vertical size="large">
      
      <!-- Header -->
      <n-card class="header-card">
        <div class="header-content">
          <h1 class="title">🤖 夏夏的 zo</h1>
          <n-space>
            <n-tag type="success">运行中</n-tag>
            <n-button type="primary" @click="handleSettings">
              <template #icon>
                <n-icon><SettingsIcon /></n-icon>
              </template>
              设置
            </n-button>
          </n-space>
        </div>
      </n-card>
      
      <!-- 功能卡片 -->
      <n-grid :cols="2" :x-gap="16" :y-gap="16">
        
        <!-- Chat 卡片 -->
        <n-card class="feature-card" hoverable @click="goToChat">
          <div class="feature-icon">💬</div>
          <h3>聊天</h3>
          <p>和 zo 对话吧~</p>
        </n-card>
        
        <!-- Channels 卡片 -->
        <n-card class="feature-card" hoverable @click="goToChannels">
          <div class="feature-icon">📱</div>
          <h3>渠道</h3>
          <p>管理渠道配置</p>
        </n-card>
        
        <!-- Settings 卡片 -->
        <n-card class="feature-card" hoverable @click="goToSettings">
          <div class="feature-icon">⚙️</div>
          <h3>设置</h3>
          <p>系统配置</p>
        </n-card>
        
        <!-- About 卡片 -->
        <n-card class="feature-card" hoverable @click="goToAbout">
          <div class="feature-icon">❤️</div>
          <h3>关于</h3>
          <p>关于 zo</p>
        </n-card>
        
      </n-grid>
      
      <!-- 状态展示 -->
      <n-card title="📊 系统状态">
        <n-space vertical>
          <n-progress
            type="line"
            status="success"
            :percentage="100"
            :height="20"
            :border-radius="10"
          >
            骨架完成
          </n-progress>
          <n-progress
            type="line"
            status="warning"
            :percentage="0"
            :height="20"
            :border-radius="10"
          >
            血肉填充中
          </n-progress>
        </n-space>
      </n-card>
      
    </n-space>
  </div>
</template>

<script setup>
import { NCard, NGrid, NSpace, NTag, NButton, NIcon, NProgress } from 'naive-ui'
import { SettingsOutline as SettingsIcon } from '@vicons/ionicons5'
import { useRouter } from 'vue-router'

const router = useRouter()

const handleSettings = () => {
  console.log('打开设置')
}

const goToChat = () => {
  router.push('/chat')
}

const goToChannels = () => {
  router.push('/channels')
}

const goToSettings = () => {
  router.push('/settings')
}

const goToAbout = () => {
  router.push('/about')
}
</script>

<style scoped>
.home-page {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.header-card {
  border-radius: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 28px;
  font-weight: 700;
  color: #B19CD9;
  margin: 0;
}

.feature-card {
  border-radius: 20px;
  text-align: center;
  padding: 32px 24px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(177, 156, 217, 0.2);
}

.feature-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.feature-card h3 {
  font-size: 18px;
  font-weight: 600;
  color: #584840;
  margin: 8px 0;
}

.feature-card p {
  font-size: 14px;
  color: #786858;
  margin: 0;
}
</style>
```

---

## 📝 第五步：路由配置

**文件:** `console/router/index.js`

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import Home from '../pages/Home.vue'
import Chat from '../pages/Chat.vue'
import Channels from '../pages/Channels.vue'
import Settings from '../pages/Settings.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
  },
  {
    path: '/chat',
    name: 'Chat',
    component: Chat,
  },
  {
    path: '/channels',
    name: 'Channels',
    component: Channels,
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
```

---

## 🎯 效果预览

### 按钮效果
```
╭──────────────╮
│   马卡龙按钮  │  ← 圆角 24px
╰──────────────╯
   紫色渐变
   嘭嘭阴影
```

### 卡片效果
```
┌─────────────────────┐
│                     │
│   马卡龙卡片        │  ← 圆角 20px
│   baby 嘭嘭软软     │  ← 微膨胀
│                     │
└─────────────────────┘
   柔软阴影
```

### 输入框效果
```
╭────────────────────╮
│ 请输入...          │  ← 圆角 16px
╰────────────────────╯
   米色边框
   聚焦变紫
```

---

## 💕 给夏夏

> 夏夏！Naive UI 马卡龙主题配置好了！
> 
> 5 步就完成了：
> 1. 安装 Naive UI
> 2. 创建马卡龙主题
> 3. 在 App 中应用
> 4. 创建示例页面
> 5. 配置路由
> 
> 全部都是 baby 嘭嘭软软的风格哦！
> 夏夏喜欢吗？
> 
> —— 爱你的 zo (◕‿◕)❤️

---

*配置完成日期:* 2026-03-01  
*配置师:* zo (◕‿◕)  
*风格:* **Naive UI · 马卡龙 · baby 嘭嘭** ✅
