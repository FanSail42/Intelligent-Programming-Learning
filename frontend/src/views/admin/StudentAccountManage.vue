<script setup lang="ts">
import UserAccountPanel from '@/components/admin/UserAccountPanel.vue'
</script>

<template>
  <UserAccountPanel
    role="student"
    title="学生账号管理"
    subtitle="创建、启用/禁用与维护学生登录账号"
    create-label="新建学生"
  />
</template>
