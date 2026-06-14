<script setup lang="ts">
import UserAccountPanel from '@/components/admin/UserAccountPanel.vue'
</script>

<template>
  <UserAccountPanel
    role="teacher"
    title="教师账号管理"
    subtitle="创建、启用/禁用与维护教师登录账号"
    create-label="新建教师"
  />
</template>
