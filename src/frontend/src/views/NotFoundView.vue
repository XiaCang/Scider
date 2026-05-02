<template>
  <section class="not-found panel-surface">
    <h1>页面未找到</h1>
    <p>你访问的页面不存在。</p>
    <router-link to="/app/library">返回文献库</router-link>
  </section>
</template>

<style scoped>
.not-found {
  width: min(100%, 640px);
  margin: 6rem auto;
  padding: 2rem;
  border-radius: 28px;
  text-align: center;
}

.not-found h1 {
  margin-bottom: 0.8rem;
}

.not-found p {
  color: var(--text-secondary);
}

.not-found a {
  display: inline-flex;
  margin-top: 1rem;
  color: var(--brand);
}
</style>
