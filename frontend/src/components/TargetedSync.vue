<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { API_BASE_URL } from '../config';
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { RefreshCw, Calendar as CalendarIcon } from 'lucide-vue-next'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { cn } from '@/lib/utils'
import { type DateValue, DateFormatter, getLocalTimeZone } from '@internationalized/date'

const developers = ref<{ id: number; name: string }[]>([]);
const selectedDeveloper = ref<{ id: number; name: string } | null>(null);
const selectedDate = ref<DateValue | undefined>(undefined);
const loading = ref(false);
const message = ref('');
const visible = ref(false);
const selectedDeveloperName = ref<string>('');
const isCalendarOpen = ref(false);

const emit = defineEmits(['dataUpdated']);

const df = new DateFormatter('en-US', {
  dateStyle: 'long',
})

const onDeveloperSelect = (name: string) => {
  const dev = developers.value.find((d) => d.name === name);
  selectedDeveloper.value = dev || null;
};

const handleDateSelect = (v: DateValue | undefined) => {
    if (v) {
        isCalendarOpen.value = false;
    }
};

const fetchDevelopers = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/developers/`);
    developers.value = await response.json();
  } catch (error) {
    console.error('Failed to fetch developers:', error);
  }
};

const handleSync = async () => {
  loading.value = true;
  message.value = '';
  try {
    // DateValue .toString() returns YYYY-MM-DD by default
    const apiDate = selectedDate.value ? selectedDate.value.toString() : null;
    
    const response = await fetch(`${API_BASE_URL}/sync/target`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        developer_id: selectedDeveloper.value ? selectedDeveloper.value.id : null,
        date: apiDate,
      }),
    });

    if (response.ok) {
        message.value = 'Sync successful!';
        emit('dataUpdated');
    } else {
      const errorText = await response.text();
      message.value = `Error: ${errorText}`;
    }
  } catch (error) {
    message.value = 'A network error occurred.';
  } finally {
    loading.value = false;
  }
};

watch(visible, (isOpen) => {
  if (isOpen) {
    fetchDevelopers();
  }
});
</script>

<template>
  <Dialog v-model:open="visible">
    <DialogTrigger as-child>
      <Button variant="outline" size="default">
        <RefreshCw class="mr-2 h-4 w-4" /> Targeted Sync
      </Button>
    </DialogTrigger>
    <DialogContent class="sm:max-w-[425px] overflow-visible">
      <DialogHeader>
        <DialogTitle>Targeted Sync</DialogTitle>
        <DialogDescription>
          Select a developer and/or a date to sync manually.
        </DialogDescription>
      </DialogHeader>

      <div class="grid gap-4 py-4">
        <div class="grid flex-col gap-2">
           <Label for="dev">Developer</Label>
           <Select v-model="selectedDeveloperName" @update:modelValue="onDeveloperSelect">
              <SelectTrigger>
                <SelectValue placeholder="Select a Developer" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem v-for="dev in developers" :key="dev.id" :value="dev.name">
                  {{ dev.name }}
                </SelectItem>
              </SelectContent>
           </Select>
        </div>

        <div class="grid flex-col gap-2">
           <Label>Date</Label>
           <Popover v-model:open="isCalendarOpen">
            <PopoverTrigger as-child>
              <Button
                variant="outline"
                :class="cn(
                  'w-full justify-start text-left font-normal',
                  !selectedDate && 'text-muted-foreground'
                )"
              >
                <CalendarIcon class="mr-2 h-4 w-4" />
                <span>{{ selectedDate ? df.format(selectedDate.toDate(getLocalTimeZone())) : "Pick a date" }}</span>
              </Button>
            </PopoverTrigger>
            <PopoverContent class="w-auto p-0">
              <Calendar 
                v-model="selectedDate" 
                mode="single" 
                class="rounded-md border"
                @update:modelValue="handleDateSelect"
              />
            </PopoverContent>
           </Popover>
        </div>
      </div>

      <div v-if="message" class="mb-4">
         <Alert :variant="message.includes('Error') ? 'destructive' : 'default'">
           <AlertTitle>{{ message.includes('Error') ? 'Error' : 'Status' }}</AlertTitle>
           <AlertDescription>{{ message }}</AlertDescription>
         </Alert>
      </div>

      <DialogFooter>
         <Button variant="secondary" @click="visible = false">Cancel</Button>
         <Button @click="handleSync" :disabled="loading">
            <span v-if="loading">Syncing...</span>
            <span v-else>Sync</span>
         </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
