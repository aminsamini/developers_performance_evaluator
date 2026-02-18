<script setup lang="ts">
import type { DialogTriggerProps } from "reka-ui"
import { DialogTrigger } from "reka-ui"

interface Props extends DialogTriggerProps {}

const props = withDefaults(defineProps<Props>(), {
  asChild: false,
})
</script>

<template>
  <DialogTrigger v-bind="props">
    <slot />
  </DialogTrigger>
</template>
