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
const syncResults = ref<any[]>([]);
const syncDone = ref(false);
const expandedErrors = ref<number[]>([]);
const visible = ref(false);

const toggleExpand = (index: number) => {
  const idx = expandedErrors.value.indexOf(index);
  if (idx >= 0) expandedErrors.value.splice(idx, 1);
  else expandedErrors.value.push(index);
};
const selectedDeveloperName = ref<string>('');
const isCalendarOpen = ref(false);

const syncGithub = ref(true);
const syncWakatime = ref(true);

const emit = defineEmits(['dataUpdated']);

const props = withDefaults(defineProps<{ onOpen?: () => void; hideTrigger?: boolean }>(), { onOpen: undefined, hideTrigger: false });

const openDialog = () => {
  visible.value = true;
  setTimeout(() => { props.onOpen?.(); }, 50);
};

defineExpose({ openDialog });

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
  syncResults.value = [];
  syncDone.value = false;
  expandedErrors.value = [];
  try {
    const apiDate = selectedDate.value ? selectedDate.value.toString() : null;

    const response = await fetch(`${API_BASE_URL}/sync/target`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        developer_id: selectedDeveloper.value ? selectedDeveloper.value.id : null,
        date_from: apiDate,
        date_to: apiDate,
        sync_github: syncGithub.value,
        sync_wakatime: syncWakatime.value
      }),
    });

    if (response.ok) {
        const data = await response.json();
        const results = data.results || [];
        syncResults.value = results;
        syncDone.value = true;
        const errors = results.filter((r: any) => r.status === 'error');
        const successes = results.filter((r: any) => !r.status || r.status !== 'error');

        if (errors.length > 0) {
          message.value = `Sync completed: ${successes.length} succeeded, ${errors.length} failed.`;
        } else if (successes.length > 0) {
          message.value = `Sync successful! ${successes.length} developer(s) synced.`;
        } else {
          message.value = 'No data synced. Check developer/repo configuration.';
        }
        triggerRefresh();
        emit('dataUpdated');
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
  <Button v-if="!hideTrigger" variant="outline" class="w-full justify-start" @click="openDialog">
    <RefreshCw class="mr-2 h-4 w-4" /> Targeted Sync
  </Button>
  <Dialog v-model:open="visible">
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
         <Alert :variant="message.includes('Error') || message.includes('failed') ? 'destructive' : 'default'">
           <AlertTitle>{{ message.includes('Error') || message.includes('failed') ? 'Error' : 'Status' }}</AlertTitle>
           <AlertDescription>{{ message }}</AlertDescription>
         </Alert>
      </div>

      <!-- Sync Results -->
      <div v-if="syncResults.length > 0" class="mb-4 max-h-48 overflow-y-auto">
        <div class="text-xs font-medium mb-2 text-muted-foreground">Results:</div>
        <div v-for="(r, i) in syncResults" :key="i" class="text-xs py-1.5 border-b last:border-0">
          <div class="flex items-center justify-between">
            <span class="font-medium">{{ r.developer }}</span>
            <span v-if="r.status === 'error'" class="text-red-500 cursor-pointer flex items-center gap-1" @click="toggleExpand(i)">
              ❌ Error
              <svg :class="['h-3 w-3 transition-transform', expandedErrors.includes(i) ? 'rotate-180' : '']" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </span>
            <span v-else class="text-green-600">✅ {{ r.commits }} commits, {{ r.coding_time }}</span>
          </div>
          <div v-if="r.status === 'error' && expandedErrors.includes(i)" class="mt-1.5 p-2 rounded bg-red-50 dark:bg-red-950/30 text-red-600 dark:text-red-400 text-[11px] font-mono break-all">
            {{ r.error }}
          </div>
        </div>
      </div>

      <DialogFooter>
         <Button v-if="syncDone" variant="secondary" @click="visible = false; syncDone = false; syncResults = []; message = ''">Close</Button>
         <template v-else>
           <Button variant="secondary" @click="visible = false">Cancel</Button>
           <Button @click="handleSync" :disabled="loading">
              <span v-if="loading">Syncing...</span>
              <span v-else>Sync</span>
           </Button>
         </template>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
