<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'

const props = defineProps<{
  content: string
}>()

marked.setOptions({
  breaks: true,
  gfm: true,
})

const html = computed(() => {
  if (!props.content) return ''
  return marked.parse(props.content, { async: false }) as string
})
</script>

<template>
  <div class="md-body" v-html="html" />
</template>

<style scoped>
.md-body {
  line-height: 1.7;
  font-size: 14px;
  word-break: break-word;
}

.md-body :deep(h2),
.md-body :deep(h3),
.md-body :deep(h4) {
  margin: 14px 0 8px;
  font-weight: 600;
  color: #303133;
}

.md-body :deep(h2) {
  font-size: 16px;
  padding-bottom: 4px;
  border-bottom: 1px solid #ebeef5;
}

.md-body :deep(h3) {
  font-size: 15px;
}

.md-body :deep(p) {
  margin: 8px 0;
}

.md-body :deep(ul),
.md-body :deep(ol) {
  margin: 8px 0;
  padding-left: 1.4em;
}

.md-body :deep(li) {
  margin: 4px 0;
}

.md-body :deep(code) {
  padding: 2px 6px;
  border-radius: 4px;
  background: #eef1f6;
  font-family: Consolas, 'Courier New', monospace;
  font-size: 13px;
}

.md-body :deep(pre) {
  margin: 10px 0;
  padding: 12px;
  border-radius: 8px;
  background: #1e1e1e;
  overflow-x: auto;
}

.md-body :deep(pre code) {
  padding: 0;
  background: transparent;
  color: #e6edf3;
  font-size: 13px;
}

.md-body :deep(blockquote) {
  margin: 8px 0;
  padding: 8px 12px;
  border-left: 3px solid #409eff;
  background: #ecf5ff;
  color: #606266;
}

.md-body :deep(strong) {
  font-weight: 600;
  color: #303133;
}
</style>
