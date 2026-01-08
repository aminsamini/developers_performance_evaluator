<script setup lang="ts">
</script>

<template>
  <div class="min-h-screen bg-background py-6">
    <router-view></router-view>
  </div>
</template>

<style>
/* Basic reset/global styles if needed, mostly handled by Tailwind */
body {
  @apply bg-background text-foreground;
}
</style>
