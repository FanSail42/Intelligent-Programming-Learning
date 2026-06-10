<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { logoutApi } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const menus = computed(() => {
  if (auth.role === 'student') {
    return [
      { path: '/student/courses', title: '我的课程' },
      { path: '/student/browse', title: '选课查询' },
      { path: '/student/chat', title: 'AI 对话' },
      { path: '/student/code', title: '代码讲解' },
      { path: '/student/dashboard', title: '学习仪表盘' },
      { path: '/student/wrong-book', title: '错题本' },
    ]
  }
  const items = [
    { path: '/teacher/courses', title: '课程管理' },
    { path: '/teacher/materials', title: '课程资料' },
    { path: '/teacher/warehouses', title: '资料仓库' },
  ]
  return items
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
</script>

<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="logo">慧编学伴</div>
      <el-menu :default-active="route.path" router>
        <el-menu-item v-for="item in menus" :key="item.path" :index="item.path">
          {{ item.title }}
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <span>{{ auth.user?.username }}（{{ auth.role }}）</span>
        <el-button link type="primary" @click="handleLogout">退出</el-button>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  min-height: 100vh;
}

.aside {
  background: #fff;
  border-right: 1px solid #ebeef5;
}

.logo {
  padding: 20px 16px;
  font-weight: 700;
  color: #409eff;
  border-bottom: 1px solid #ebeef5;
}

.header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
}

.main {
  background: #f5f7fa;
}
</style>
