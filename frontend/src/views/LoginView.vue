<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

async function onSubmit() {
  loading.value = true
  try {
    const user = await auth.login(form.username, form.password)
    ElMessage.success('登录成功')
    if (user?.role === 'student') {
      await router.push('/student/courses')
    } else if (user?.role === 'teacher') {
      await router.push('/teacher/courses')
    } else {
      await router.push('/teacher/courses')
    }
  } catch {
    // error handled by axios interceptor
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <el-card class="login-card">
      <template #header>
        <h2>慧编学伴 · 登录</h2>
      </template>
      <el-form label-width="80px" @submit.prevent="onSubmit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="stu / tea / adm" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" native-type="submit" style="width: 100%">
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <p class="hint">演示账号见 docs/deploy.md（需先运行 seed_demo.py）</p>
    </el-card>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eef5ff, #f5f7fa);
}

.login-card {
  width: 420px;
}

.login-card h2 {
  margin: 0;
  text-align: center;
  color: #409eff;
}

.hint {
  font-size: 12px;
  color: #909399;
  text-align: center;
  margin: 0;
}
</style>
