<script setup lang="ts">
import Dashboard from './components/Dashboard.vue'
</script>

<template>
  <div class="min-h-screen bg-background py-6">
    <Dashboard />
  </div>
</template>

<style>
/* Basic reset/global styles if needed, mostly handled by Tailwind */
body {
  @apply bg-background text-foreground;
}
</style>
