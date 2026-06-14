<script setup lang="ts">
withDefaults(
  defineProps<{
    size?: 'sm' | 'md' | 'lg'
    showText?: boolean
    showTagline?: boolean
    light?: boolean
  }>(),
  {
    size: 'md',
    showText: true,
    showTagline: false,
    light: false,
  },
)
</script>

<template>
  <div class="app-logo" :class="[size, { light }]">
    <img src="/logo.svg" alt="慧编学伴" class="logo-img" />
    <div v-if="showText" class="logo-text">
      <span class="brand">慧编学伴</span>
      <span v-if="showTagline" class="tagline">智能编程学习助教</span>
    </div>
  </div>
</template>

<style scoped>
.app-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-img {
  object-fit: contain;
  flex-shrink: 0;
}

.sm .logo-img {
  width: 28px;
  height: 28px;
}

.md .logo-img {
  width: 36px;
  height: 36px;
}

.lg .logo-img {
  width: 56px;
  height: 56px;
}

.logo-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand {
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1.2;
}

.tagline {
  font-size: 11px;
  opacity: 0.75;
  line-height: 1.3;
}

.sm .brand {
  font-size: 14px;
}

.md .brand {
  font-size: 16px;
}

.lg .brand {
  font-size: 22px;
}

.md .tagline,
.lg .tagline {
  font-size: 12px;
}

.app-logo:not(.light) .brand {
  color: #1e3a8a;
}

.app-logo:not(.light) .tagline {
  color: #64748b;
}

.app-logo.light .brand,
.app-logo.light .tagline {
  color: #fff;
}

.app-logo.light .tagline {
  opacity: 0.88;
}
</style>
