<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const timezones = [
  'Asia/Tehran',
  'UTC',
  'Europe/London',
  'Europe/Berlin',
  'America/New_York',
  'America/Los_Angeles',
  'Asia/Dubai',
  'Asia/Tokyo'
];

// Default to Tehran as requested
const selectedTimezone = ref('Asia/Tehran');

const emit = defineEmits(['update:timezone']);

// Update logic to handle shadcn update behavior if needed,
// usually v-model works directly.
onMounted(() => {
  const saved = localStorage.getItem('performance_app_timezone');
  if (saved && timezones.includes(saved)) {
    selectedTimezone.value = saved;
  }
  emit('update:timezone', selectedTimezone.value);
});

watch(selectedTimezone, (newVal) => {
  localStorage.setItem('performance_app_timezone', newVal);
  emit('update:timezone', newVal);
});
</script>

<template>
  <div class="flex items-center gap-2">
    <Select v-model="selectedTimezone">
      <SelectTrigger class="w-full">
        <SelectValue placeholder="Select timezone" />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          <SelectLabel>Regional Timezones</SelectLabel>
          <SelectItem v-for="tz in timezones" :key="tz" :value="tz">
            {{ tz }}
          </SelectItem>
        </SelectGroup>
      </SelectContent>
    </Select>
  </div>
</template>
