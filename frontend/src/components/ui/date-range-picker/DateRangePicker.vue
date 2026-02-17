<script setup lang="ts">
import { ref, computed } from 'vue'
import { Calendar as CalendarIcon } from 'lucide-vue-next'
import { DateFormatter, type DateValue, getLocalTimeZone } from '@internationalized/date'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'

const props = defineProps<{
  modelValue: { start?: DateValue; end?: DateValue }
  class?: string
}>()

const emit = defineEmits(['update:modelValue'])

const df = new DateFormatter('en-US', {
  dateStyle: 'medium',
})

const value = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})
</script>

<template>
  <div :class="cn('grid gap-2', props.class)">
    <Popover>
      <PopoverTrigger as-child>
        <Button
          id="date"
          type="button"
          :variant="'outline'"
          :class="cn(
            'w-[300px] justify-start text-left font-normal',
            !value.start && 'text-muted-foreground',
          )"
        >
          <CalendarIcon class="mr-2 h-4 w-4" />
          <template v-if="value.start">
            <template v-if="value.end">
              {{ df.format(value.start.toDate(getLocalTimeZone())) }} - {{ df.format(value.end.toDate(getLocalTimeZone())) }}
            </template>
            <template v-else>
              {{ df.format(value.start.toDate(getLocalTimeZone())) }}
            </template>
          </template>
          <template v-else>
            Pick a date
          </template>
        </Button>
      </PopoverTrigger>
      <PopoverContent class="w-auto p-0 z-[200]" align="start">
        <!-- <Calendar
          v-model="value"
          type="range"
          initial-focus
          :numberOfMonths="2"
        /> -->
        <div class="p-4 bg-white border">DEBUG: POPOVER OPENED</div>
        <!-- Note: Calendar type is inferred from v-model value usually, but passing an object implies Range. 
             Ideally we pass type="range" prop explicitly to CalendarRoot via Calendar -->
      </PopoverContent>
    </Popover>
  </div>
</template>
