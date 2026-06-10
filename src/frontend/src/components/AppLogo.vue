<template>
  <div class="app-logo">
    <img 
      src="../assets/logo.png" 
      alt="Scider Logo" 
      class="app-logo__img"
    />
    
    <div class="app-logo__text">
      <strong>Scider</strong>
      <small>Academic Reading Companion</small>
    </div>
  </div>
</template>

<style scoped>
.app-logo {
  display: inline-flex;
  align-items: center;
  gap: 0.9rem;
}

/* 新的图片样式控制 */
.app-logo__img {
  width: 2rem;       /* 保持与原图标一致的宽度 */
  height: 2rem;      /* 保持与原图标一致的高度 */
  object-fit: contain; /* 确保图片比例不失真 */
  /* 如果你的图片没有自带圆角，可以按需开启下方属性 */
  border-radius: 0.72rem;
}

.app-logo__text {
  display: flex;
  flex-direction: column;
  gap: 0.08rem;
}

.app-logo__text strong {
  font-size: 1.1rem;
  line-height: 1;
  letter-spacing: -0.03em;
  color: #173668; /* 建议给文字一个深色，保持对比度 */
}

.app-logo__text small {
  color: var(--text-tertiary, #666); /* 增加备用色以防变量失效 */
  font-size: 0.72rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
</style>