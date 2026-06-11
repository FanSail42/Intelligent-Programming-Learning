<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowDown } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { logoutApi } from '@/api/auth'
import AppLogo from '@/components/AppLogo.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

type FlatMenuItem = { path: string; title: string }
type GroupMenuItem = { title: string; children: FlatMenuItem[] }
type MenuItem = FlatMenuItem | GroupMenuItem

function isGroup(item: MenuItem): item is GroupMenuItem {
  return 'children' in item
}

const menus = computed<MenuItem[]>(() => {
  if (auth.role === 'student') {
    return [
      {
        title: '课程学习',
        children: [
          { path: '/student/courses', title: '我的课程' },
          { path: '/student/browse', title: '选课查询' },
        ],
      },
      {
        title: 'AI 辅导',
        children: [
          { path: '/student/chat', title: 'AI 对话' },
          { path: '/student/code', title: '代码讲解' },
        ],
      },
      {
        title: '学情中心',
        children: [
          { path: '/student/dashboard', title: '学习仪表盘' },
          { path: '/student/wrong-book', title: '错题本' },
        ],
      },
      {
        title: '账户',
        children: [{ path: '/profile', title: '个人中心' }],
      },
    ]
  }

  const items: MenuItem[] = []

  if (auth.role === 'admin') {
    items.push({
      title: '系统管理',
      children: [
        { path: '/admin/overview', title: '管理概览' },
        { path: '/admin/students', title: '学生账号' },
        { path: '/admin/teachers', title: '教师账号' },
        { path: '/admin/logs', title: '操作日志' },
      ],
    })
    items.push({
      title: 'AI 管理',
      children: [
        { path: '/admin/ai-models', title: 'AI 模型管理' },
        { path: '/admin/ai-usage', title: 'AI 用量监控' },
      ],
    })
  }

  items.push(
    {
      title: '课程教学',
      children: [
        { path: '/teacher/courses', title: '课程管理' },
        { path: '/teacher/dashboard', title: '班级学情' },
      ],
    },
    {
      title: '资料管理',
      children: [
        { path: '/teacher/materials', title: '课程资料' },
        { path: '/teacher/warehouses', title: '资料仓库' },
      ],
    },
    {
      title: '账户',
      children: [{ path: '/profile', title: '个人中心' }],
    },
  )

  return items
})

const activeMenu = computed(() => route.path)

const roleLabel = computed(() => {
  const map: Record<string, string> = {
    student: '学生',
    teacher: '教师',
    admin: '管理员',
  }
  return map[auth.role ?? ''] ?? auth.role
})

async function handleLogout() {
  try {
    await logoutApi()
  } catch {
    // ignore
  }
  auth.logout()
  router.push('/login')
}

function goProfile() {
  router.push('/profile')
}
</script>

<template>
  <div class="layout">
    <aside class="aside">
      <div class="logo-wrap">
        <AppLogo size="sm" light />
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        class="side-menu"
        background-color="transparent"
        text-color="#cbd5e1"
        active-text-color="#ffffff"
      >
        <template v-for="item in menus" :key="isGroup(item) ? item.title : item.path">
          <el-sub-menu v-if="isGroup(item)" :index="item.title">
            <template #title>{{ item.title }}</template>
            <el-menu-item
              v-for="child in item.children"
              :key="child.path"
              :index="child.path"
            >
              {{ child.title }}
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="item.path">
            {{ item.title }}
          </el-menu-item>
        </template>
      </el-menu>
    </aside>

    <div class="main-wrapper">
      <header class="header">
        <el-dropdown trigger="click" @command="(cmd: string) => cmd === 'profile' ? goProfile() : handleLogout()">
          <div class="header-user">
            <span class="user-avatar">{{ (auth.user?.username ?? '?').slice(0, 1).toUpperCase() }}</span>
            <span class="user-name">{{ auth.user?.username }}</span>
            <el-tag size="small" type="info" effect="plain">{{ roleLabel }}</el-tag>
            <el-icon class="user-arrow"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人中心</el-dropdown-item>
              <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </header>
      <main class="main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
}

.aside {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 200;
  width: 220px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--hb-sidebar-bg);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: 4px 0 24px rgba(15, 23, 42, 0.15);
}

.logo-wrap {
  flex-shrink: 0;
  padding: 18px 16px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.side-menu {
  flex: 1;
  overflow-x: hidden;
  overflow-y: auto;
  border-right: none;
  padding: 8px 0 16px;
}

.side-menu :deep(.el-sub-menu__title),
.side-menu :deep(.el-menu-item) {
  height: 44px;
  line-height: 44px;
  margin: 2px 8px;
  border-radius: 8px;
}

.side-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(37, 99, 235, 0.85), rgba(6, 182, 212, 0.55)) !important;
  font-weight: 600;
}

.side-menu :deep(.el-sub-menu__title:hover),
.side-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.06) !important;
}

.side-menu :deep(.el-sub-menu .el-menu-item) {
  min-width: auto;
  padding-left: 48px !important;
}

.main-wrapper {
  margin-left: 220px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  height: 56px;
  padding: 0 24px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--hb-border);
}

.header-user {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 10px;
  transition: background 0.2s ease;
}

.header-user:hover {
  background: #f1f5f9;
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2563eb, #06b6d4);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-arrow {
  color: var(--hb-text-secondary);
  font-size: 12px;
}

.user-name {
  font-weight: 500;
  color: var(--hb-text);
}

.main {
  flex: 1;
  padding: 20px 24px 28px;
  background: var(--hb-bg);
}
</style>
