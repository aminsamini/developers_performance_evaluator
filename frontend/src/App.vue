<script setup lang="ts">
import NavBar from '@/components/NavBar.vue';
</script>

<template>
  <div class="min-h-screen bg-background pb-6 pt-24">
    <NavBar />
    <router-view></router-view>
  </div>
</template>

<style>
/* Basic reset/global styles if needed, mostly handled by Tailwind */
body {
  @apply bg-background text-foreground;
}
</style>
