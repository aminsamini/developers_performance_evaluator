<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { API_BASE_URL } from '../config';
import { useGlobalState, type Developer } from '@/composables/useGlobalState';
import { useToast } from '@/components/ui/toast/use-toast';
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
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

const { developers, fetchDevelopers, triggerRefresh } = useGlobalState();
const { toast } = useToast();

const selectedDeveloper = ref<Developer | null>(null);
const selectedDate = ref<DateValue | undefined>(undefined);
const loading = ref(false);
const message = ref('');
const visible = ref(false);
const selectedDeveloperName = ref<string>('');
const isCalendarOpen = ref(false);

const syncGithub = ref(true);
const syncWakatime = ref(true);

const emit = defineEmits(['dataUpdated']);

const df = new DateFormatter('en-US', {
  dateStyle: 'long',
})

const hasWakaTimeKey = computed(() => {
  return selectedDeveloper.value && !!selectedDeveloper.value.wakatime_api_key;
});

const showWakaTimeWarning = computed(() => {
  return syncWakatime.value && selectedDeveloper.value && !hasWakaTimeKey.value;
});

const onDeveloperSelect = (name: string) => {
  const dev = developers.value.find((d) => d.name === name);
  selectedDeveloper.value = dev || null;
};

const handleDateSelect = (v: DateValue | undefined) => {
    if (v) {
        isCalendarOpen.value = false;
    }
};

const handleSync = async () => {
  if (!syncGithub.value && !syncWakatime.value) {
      message.value = 'Error: Please select at least one service to sync.';
      return;
  }

  loading.value = true;
  message.value = '';
  try {
    const apiDate = selectedDate.value ? selectedDate.value.toString() : null;
    
    const response = await fetch(`${API_BASE_URL}/sync/target`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        developer_id: selectedDeveloper.value ? selectedDeveloper.value.id : null,
        date: apiDate,
        sync_github: syncGithub.value,
        sync_wakatime: syncWakatime.value
      }),
    });

    if (response.ok) {
        toast({
          title: "Sync Successful",
          description: `Metrics synced for ${selectedDeveloper.value ? selectedDeveloper.value.name : 'all developers'} on ${apiDate || 'today'}.`,
        });
        message.value = 'Sync successful!';
        triggerRefresh();
        emit('dataUpdated');
        visible.value = false; // Close dialog on success
    } else {
        const errorText = await response.text();
        message.value = `Error: ${errorText}`;
        toast({
          title: "Sync Failed",
          description: errorText,
          variant: "destructive",
        });
    }
  } catch (error) {
    message.value = 'A network error occurred.';
    toast({
      title: "Network Error",
      description: "Could not connect to the backend server.",
      variant: "destructive",
    });
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
              <SelectContent class="z-[110]">
                <SelectItem v-for="dev in developers" :key="dev.id" :value="dev.name">
                  {{ dev.name }}
                </SelectItem>
              </SelectContent>
           </Select>
           <p v-if="showWakaTimeWarning" class="text-[11px] text-amber-600 mt-1">
             Warning: This developer has no WakaTime API key set.
           </p>
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
            <PopoverContent class="w-auto p-0 z-[110]">
              <Calendar 
                v-model="selectedDate" 
                mode="single" 
                class="rounded-md border"
                @update:modelValue="handleDateSelect"
              />
            </PopoverContent>
           </Popover>
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
            <span v-else>Sync</span>
         </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
