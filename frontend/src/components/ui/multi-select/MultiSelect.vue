<script setup lang="ts">
import { ref, computed } from 'vue'
import { Check, ChevronsUpDown, X } from 'lucide-vue-next'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'

interface Option {
  label: string
  value: any
}

const props = defineProps<{
  options: Option[]
  modelValue: any[]
  placeholder?: string
  class?: string
}>()

const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const searchQuery = ref('')

const selectedLabels = computed(() => {
  return props.options
    .filter(opt => props.modelValue.includes(opt.value))
    .map(opt => opt.label)
})

const filteredOptions = computed(() => {
  if (!searchQuery.value) return props.options
  return props.options.filter(opt => 
    opt.label.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const toggleOption = (value: any) => {
  const newValue = [...props.modelValue]
  const index = newValue.indexOf(value)
  if (index >= 0) {
    newValue.splice(index, 1)
  } else {
    newValue.push(value)
  }
  emit('update:modelValue', newValue)
}

const removeItem = (value: any) => {
  const newValue = props.modelValue.filter(v => v !== value)
  emit('update:modelValue', newValue)
}
</script>

<template>
  <Popover v-model:open="open">
    <PopoverTrigger as-child>
      <Button
        variant="outline"
        role="combobox"
        :aria-expanded="open"
        :class="cn('w-full justify-between h-auto min-h-10 py-2', props.class)"
      >
        <div class="flex flex-wrap gap-1 items-center">
            <span v-if="modelValue.length === 0" class="text-muted-foreground font-normal">
                {{ placeholder || 'Select items...' }}
            </span>
            <template v-else>
                <Badge v-for="val in modelValue.slice(0, 3)" :key="val" variant="secondary" class="mr-1">
                    {{ options.find(o => o.value === val)?.label }}
                    <X class="ml-1 h-3 w-3 cursor-pointer" @click.stop="removeItem(val)" />
                </Badge>
                <span v-if="modelValue.length > 3" class="text-xs text-muted-foreground">
                    +{{ modelValue.length - 3 }} more
                </span>
            </template>
        </div>
        <ChevronsUpDown class="ml-2 h-4 w-4 shrink-0 opacity-50" />
      </Button>
    </PopoverTrigger>
    <PopoverContent class="w-[300px] p-0">
      <div class="p-2 border-b">
        <Input v-model="searchQuery" placeholder="Search..." class="h-8" />
      </div>
      <div class="max-h-[300px] overflow-auto p-1">
          <div 
            v-if="filteredOptions.length === 0" 
            class="py-6 text-center text-sm text-muted-foreground"
          >
            No results found.
          </div>
          <div
            v-for="option in filteredOptions"
            :key="option.value"
            @click="toggleOption(option.value)"
            :class="cn(
                'relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent hover:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
                modelValue.includes(option.value) ? 'bg-accent/50' : ''
            )"
          >
            <div :class="cn('mr-2 flex h-4 w-4 items-center justify-center rounded-sm border border-primary', modelValue.includes(option.value) ? 'bg-primary text-primary-foreground' : 'opacity-50 [&_svg]:invisible')">
              <Check class="h-4 w-4" />
            </div>
            <span>{{ option.label }}</span>
          </div>
      </div>
    </PopoverContent>
  </Popover>
</template>
