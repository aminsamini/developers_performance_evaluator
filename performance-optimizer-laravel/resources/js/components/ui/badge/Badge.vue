<script setup lang="ts">
import type { HTMLAttributes } from "vue"
import type { BadgeVariants } from "."
import { Primitive, type PrimitiveProps } from "reka-ui"
import { cn } from "@/lib/utils"
import { badgeVariants } from "."

interface Props extends PrimitiveProps {
  variant?: BadgeVariants["variant"]
  class?: HTMLAttributes["class"]
}

const props = withDefaults(defineProps<Props>(), {
  as: "div",
})
</script>

<template>
  <Primitive
    :as="as"
    :as-child="asChild"
    :class="cn(badgeVariants({ variant: variant }), props.class)"
  >
    <slot />
  </Primitive>
</template>
