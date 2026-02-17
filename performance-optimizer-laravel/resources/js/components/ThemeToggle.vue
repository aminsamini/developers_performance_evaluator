<script setup lang="ts">
import { useDark, useToggle } from '@vueuse/core';
import { Button } from '@/components/ui/button';
import { Moon, Sun } from 'lucide-vue-next';

// Tailwind dark mode uses 'dark' class on html/body
const isDark = useDark({
  selector: 'body',
  attribute: 'class',
  valueDark: 'dark',
  valueLight: '',
});
const toggleDark = useToggle(isDark);
</script>

<template>
  <Button variant="ghost" size="icon" @click="toggleDark()">
    <Moon v-if="isDark" class="h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
    <Sun v-else class="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
    <span class="sr-only">Toggle theme</span>
  </Button>
</template>
