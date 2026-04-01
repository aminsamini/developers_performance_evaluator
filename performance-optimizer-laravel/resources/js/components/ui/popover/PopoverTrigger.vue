<script setup lang="ts">
import type { PopoverTriggerProps } from "reka-ui"
import { PopoverTrigger } from "reka-ui"

const props = withDefaults(defineProps<PopoverTriggerProps>(), {
  asChild: false,
})
</script>

<template>
  <PopoverTrigger v-bind="props">
    <slot />
  </PopoverTrigger>
</template>
