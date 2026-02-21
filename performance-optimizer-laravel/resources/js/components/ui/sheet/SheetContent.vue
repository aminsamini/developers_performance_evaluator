<script setup lang="ts">
import type { DialogContentEmits, DialogContentProps } from "reka-ui"
import type { HTMLAttributes } from "vue"
import type { SheetVariants } from "."
import { reactiveOmit } from "@vueuse/core"
import { X } from "lucide-vue-next"
import {
  DialogClose,
  DialogContent,
  DialogOverlay,
  DialogPortal,
  useForwardPropsEmits,
} from "reka-ui"
import { cn } from "@/lib/utils"
import { sheetVariants } from "."

interface SheetContentProps extends DialogContentProps {
  class?: HTMLAttributes["class"]
  side?: SheetVariants["side"]
}

defineOptions({
  inheritAttrs: false,
})

const props = defineProps<SheetContentProps>()

const emits = defineEmits<DialogContentEmits>()

const delegatedProps = reactiveOmit(props, "class", "side")

const forwarded = useForwardPropsEmits(delegatedProps, emits)

const sideStyles: Record<string, string> = {
  right: 'top: 0; right: 0; bottom: 0; width: 75%; max-width: 24rem; border-left: 1px solid hsl(var(--border));',
  left:  'top: 0; left: 0; bottom: 0; width: 75%; max-width: 24rem; border-right: 1px solid hsl(var(--border));',
  top:   'top: 0; left: 0; right: 0; height: auto; border-bottom: 1px solid hsl(var(--border));',
  bottom:'bottom: 0; left: 0; right: 0; height: auto; border-top: 1px solid hsl(var(--border));',
}

const panelStyle = `
  position: fixed;
  z-index: 9999;
  background-color: hsl(var(--background));
  color: hsl(var(--foreground));
  padding: 1.5rem;
  box-shadow: -4px 0 24px rgba(0,0,0,0.2);
  overflow-y: auto;
  ${sideStyles[props.side ?? 'right']}
`
</script>

<template>
  <DialogPortal>
    <DialogOverlay
      style="position: fixed; inset: 0; z-index: 9998; background-color: rgba(0,0,0,0.6);"
    />
    <DialogContent
      :class="cn(props.class)"
      :style="panelStyle"
      v-bind="{ ...forwarded, ...$attrs }"
    >
      <slot />

      <DialogClose
        style="position: absolute; right: 1rem; top: 1rem; opacity: 0.7; cursor: pointer;"
      >
        <X class="w-4 h-4" />
      </DialogClose>
    </DialogContent>
  </DialogPortal>
</template>
