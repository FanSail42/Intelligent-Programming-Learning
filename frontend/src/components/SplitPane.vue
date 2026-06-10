<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

const props = withDefaults(
  defineProps<{
    initialLeftPercent?: number
    minLeftPercent?: number
    maxLeftPercent?: number
  }>(),
  {
    initialLeftPercent: 50,
    minLeftPercent: 28,
    maxLeftPercent: 72,
  },
)

const leftPercent = ref(props.initialLeftPercent)
const dragging = ref(false)
const containerRef = ref<HTMLElement | null>(null)

function onMouseMove(e: MouseEvent) {
  if (!dragging.value || !containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  const ratio = ((e.clientX - rect.left) / rect.width) * 100
  leftPercent.value = Math.min(
    props.maxLeftPercent,
    Math.max(props.minLeftPercent, ratio),
  )
}

function stopDrag() {
  dragging.value = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

function startDrag() {
  dragging.value = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

onMounted(() => {
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', stopDrag)
})

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', stopDrag)
  stopDrag()
})
</script>

<template>
  <div ref="containerRef" class="split-pane">
    <div class="split-left" :style="{ width: `${leftPercent}%` }">
      <slot name="left" />
    </div>
    <div
      class="split-divider"
      role="separator"
      aria-orientation="vertical"
      @mousedown.prevent="startDrag"
    />
    <div class="split-right">
      <slot name="right" />
    </div>
  </div>
</template>

<style scoped>
.split-pane {
  display: flex;
  align-items: stretch;
  gap: 0;
  min-height: 520px;
}

.split-left {
  flex-shrink: 0;
  min-width: 0;
}

.split-right {
  flex: 1;
  min-width: 0;
}

.split-divider {
  width: 8px;
  margin: 0 4px;
  cursor: col-resize;
  flex-shrink: 0;
  position: relative;
  border-radius: 4px;
  background: transparent;
  transition: background 0.15s;
}

.split-divider::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 8%;
  bottom: 8%;
  width: 2px;
  transform: translateX(-50%);
  background: #dcdfe6;
  border-radius: 1px;
}

.split-divider:hover::after {
  background: #409eff;
}

@media (max-width: 960px) {
  .split-pane {
    flex-direction: column;
  }

  .split-left {
    width: 100% !important;
  }

  .split-divider {
    width: 100%;
    height: 8px;
    margin: 8px 0;
    cursor: row-resize;
  }

  .split-divider::after {
    left: 8%;
    right: 8%;
    top: 50%;
    bottom: auto;
    width: auto;
    height: 2px;
    transform: translateY(-50%);
  }
}
</style>
