<template>
  <section class="not-found panel-surface">
    <h1>Page not found</h1>
    <p>The page you are looking for does not exist yet.</p>
    <router-link to="/app/library">Back to library</router-link>
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
