<template>
  <div class="forbidden">
    <el-result icon="warning" title="403" sub-title="您没有权限访问此页面">
      <template #extra>
        <el-button type="primary" @click="$router.push('/login')">返回登录</el-button>
      </template>
    </el-result>
  </div>
</template>

<style scoped>
.forbidden {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
