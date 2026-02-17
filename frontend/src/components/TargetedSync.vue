<script setup lang="ts">
import { ref, watch } from 'vue';
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
import { RefreshCw } from 'lucide-vue-next'
import DateRangePicker from '@/components/ui/date-range-picker/DateRangePicker.vue'
import { type DateValue } from '@internationalized/date'

const developers = ref<{ id: number; name: string }[]>([]);
const selectedDeveloper = ref<{ id: number; name: string } | null>(null);
const selectedDateRange = ref<any>({ start: undefined, end: undefined });
const loading = ref(false);
const message = ref('');
const visible = ref(false);
const selectedDeveloperName = ref<string>('');

const syncGithub = ref(true);
const syncWakatime = ref(true);

const emit = defineEmits(['dataUpdated']);

const onDeveloperSelect = (val: any) => {
  const name = val as string;
  const dev = developers.value.find((d) => d.name === name);
  selectedDeveloper.value = dev || null;
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
  if (!syncGithub.value && !syncWakatime.value) {
      message.value = 'Error: Please select at least one service to sync.';
      return;
  }
  
  if (!selectedDateRange.value.start) {
       message.value = 'Error: Please select a date range.';
       return;
  }

  loading.value = true;
  message.value = '';
  try {
    const startStr = selectedDateRange.value.start.toString();
    // Use start date as end date if end is missing (single day selection)
    const endStr = selectedDateRange.value.end ? selectedDateRange.value.end.toString() : startStr;
    
    const response = await fetch(`${API_BASE_URL}/sync/target`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        developer_id: selectedDeveloper.value ? selectedDeveloper.value.id : null,
        date_from: startStr,
        date_to: endStr,
        sync_github: syncGithub.value,
        sync_wakatime: syncWakatime.value
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
      <Button variant="outline" class="w-full justify-start">
        <RefreshCw class="mr-2 h-4 w-4" /> Targeted Sync
      </Button>
    </DialogTrigger>
    <DialogContent class="sm:max-w-[500px] overflow-visible z-[150]">
      <DialogHeader>
        <DialogTitle>Targeted Sync</DialogTitle>
        <DialogDescription>
          Select a developer and/or a date range to sync manually.
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
           <Label>Date Range</Label>
           <DateRangePicker v-model="selectedDateRange" class="w-full" />
        </div>
        
        <div class="grid flex-col gap-2">
            <Label>Sync Options</Label>
            <div class="flex items-center gap-4">
                <div class="flex items-center space-x-2">
                    <input type="checkbox" id="sync-github" v-model="syncGithub" class="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary accent-black" />
                    <Label for="sync-github" class="text-sm font-normal cursor-pointer">Sync GitHub</Label>
                </div>
                <div class="flex items-center space-x-2">
                    <input type="checkbox" id="sync-wakatime" v-model="syncWakatime" class="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary accent-black" />
                    <Label for="sync-wakatime" class="text-sm font-normal cursor-pointer">Sync WakaTime</Label>
                </div>
            </div>
            <!-- Debug State -->
            <div class="text-xs text-muted-foreground mt-1">
                Will Sync: 
                <span :class="syncGithub ? 'text-green-600' : 'text-red-500'">GitHub ({{ syncGithub }})</span>, 
                <span :class="syncWakatime ? 'text-green-600' : 'text-red-500'">WakaTime ({{ syncWakatime }})</span>
            </div>
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
            <span v-else>Sync Range</span>
         </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
