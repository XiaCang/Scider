<template>
  <div 
    class="app-logo" 
    :style="{ '--logo-size': `${size}px` }"
  >
    <img 
      src="../assets/logo.png" 
      alt="Scider 标志" 
      class="app-logo__img"
    />
    
    <div class="app-logo__text">
      <strong>Scider</strong>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps({
  // 定义 size 属性，默认值为 32
  size: {
    type: [Number, String],
    default: 32
  }
});
</script>

<style scoped>
.app-logo {
  display: inline-flex;
  align-items: center;
  /* 使用传入的 size 比例化间距 */
  gap: calc(var(--logo-size) * 0.3); 
}

.app-logo__img {
  /* 这里的宽高直接响应 size 属性 */
  width: var(--logo-size);
  height: var(--logo-size);
  object-fit: contain;
  border-radius: calc(var(--logo-size) * 0.2);
}

.app-logo__text {
  display: flex;
  flex-direction: column;
}

.app-logo__text strong {
  /* 字体大小根据图标大小自动缩放 */
  font-size: calc(var(--logo-size) * 0.6);
  line-height: 1;
  letter-spacing: -0.03em;
  color: #173668;
}
</style>