<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { Download, Loader2, Search, X } from 'lucide-vue-next';
import { API_BASE_URL } from '../config';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose
} from '@/components/ui/dialog';

interface Developer {
  id: number;
  name: string;
}

const props = defineProps<{
  developers: Developer[];
}>();

// Modal state
const isOpen = ref(false);
const isExporting = ref(false);
const exportError = ref('');

// Form state
const fromDate = ref('');
const toDate = ref('');
const selectedDeveloperIds = ref<number[]>([]);
const exportFormat = ref<'excel' | 'pdf'>('excel');
const includeCharts = ref(true);
const includeSummary = ref(true);
const groupByDeveloper = ref(false);
const includeRawWakatime = ref(false);
const developerSearch = ref('');

// Initialize with last 60 days
const initializeDates = () => {
  const today = new Date();
  const sixtyDaysAgo = new Date(today);
  sixtyDaysAgo.setDate(sixtyDaysAgo.getDate() - 60);

  toDate.value = today.toISOString().split('T')[0];
  fromDate.value = sixtyDaysAgo.toISOString().split('T')[0];
};

// Computed properties
const filteredDevelopers = computed(() => {
  if (!developerSearch.value) return props.developers;
  const search = developerSearch.value.toLowerCase();
  return props.developers.filter(d => d.name.toLowerCase().includes(search));
});

const dateRangeError = computed(() => {
  if (!fromDate.value || !toDate.value) return '';

  const from = new Date(fromDate.value);
  const to = new Date(toDate.value);

  if (to < from) {
    return 'To date must be after or equal to from date';
  }

  const diffDays = Math.ceil((to.getTime() - from.getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays > 90) {
    return 'Date range cannot exceed 90 days';
  }

  return '';
});

const selectedCount = computed(() => selectedDeveloperIds.value.length);
const totalCount = computed(() => props.developers.length);

const isFormValid = computed(() => {
  return fromDate.value &&
         toDate.value &&
         !dateRangeError.value &&
         selectedDeveloperIds.value.length > 0;
});

// Methods
const openModal = () => {
  initializeDates();
  selectedDeveloperIds.value = [];
  exportError.value = '';
  isOpen.value = true;
};

const toggleDeveloper = (id: number) => {
  const index = selectedDeveloperIds.value.indexOf(id);
  if (index === -1) {
    selectedDeveloperIds.value.push(id);
  } else {
    selectedDeveloperIds.value.splice(index, 1);
  }
};

const selectAll = () => {
  selectedDeveloperIds.value = props.developers.map(d => d.id);
};

const deselectAll = () => {
  selectedDeveloperIds.value = [];
};

const handleExport = async () => {
  if (!isFormValid.value) return;

  isExporting.value = true;
  exportError.value = '';

  try {
    const response = await fetch(`${API_BASE_URL}/export/report`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from_date: fromDate.value,
        to_date: toDate.value,
        developer_ids: selectedDeveloperIds.value,
        format: exportFormat.value,
        include_charts: includeCharts.value,
        include_summary: includeSummary.value,
        group_by_developer: groupByDeveloper.value,
        include_raw_wakatime: includeRawWakatime.value
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Export failed');
    }

    // Download the file
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;

    // Get filename from Content-Disposition header or use default
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = `performance_report.${exportFormat.value === 'excel' ? 'xlsx' : 'pdf'}`;
    if (contentDisposition) {
      const match = contentDisposition.match(/filename=(.+)/);
      if (match) filename = match[1];
    }

    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    isOpen.value = false;
  } catch (error: any) {
    exportError.value = error.message || 'Failed to generate export';
  } finally {
    isExporting.value = false;
  }
};
</script>

<template>
  <div>
    <!-- Trigger Button -->
    <Button @click="openModal" variant="outline" class="w-full justify-start">
      <Download class="mr-2 h-4 w-4" />
      Export Report
    </Button>

    <!-- Export Modal -->
    <Dialog v-model:open="isOpen">
      <DialogContent class="max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Export Performance Report</DialogTitle>
          <DialogDescription>
            Configure your export settings and download performance data.
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-6 py-4">
          <!-- Date Range Section -->
          <div class="space-y-3">
            <Label class="text-sm font-medium">Date Range</Label>
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-1">
                <Label class="text-xs text-muted-foreground">From Date</Label>
                <Input
                  type="date"
                  v-model="fromDate"
                  class="w-full"
                />
              </div>
              <div class="space-y-1">
                <Label class="text-xs text-muted-foreground">To Date</Label>
                <Input
                  type="date"
                  v-model="toDate"
                  class="w-full"
                />
              </div>
            </div>
            <p v-if="dateRangeError" class="text-xs text-red-500">
              {{ dateRangeError }}
            </p>
          </div>

          <!-- Developer Selection -->
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <Label class="text-sm font-medium">Developers</Label>
              <span class="text-xs text-muted-foreground">
                {{ selectedCount }} of {{ totalCount }} selected
              </span>
            </div>

            <!-- Search & Actions -->
            <div class="flex gap-2">
              <div class="relative flex-1">
                <Search class="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  v-model="developerSearch"
                  placeholder="Search developers..."
                  class="pl-8"
                />
              </div>
              <Button variant="outline" size="sm" @click="selectAll">All</Button>
              <Button variant="outline" size="sm" @click="deselectAll">None</Button>
            </div>

            <!-- Developer List -->
            <div class="max-h-40 overflow-y-auto border rounded-md p-2 space-y-1">
              <div
                v-for="dev in filteredDevelopers"
                :key="dev.id"
                class="flex items-center gap-2 p-2 rounded hover:bg-muted/50 cursor-pointer"
                @click="toggleDeveloper(dev.id)"
              >
                <Checkbox
                  :checked="selectedDeveloperIds.includes(dev.id)"
                  @click.stop
                />
                <span class="text-sm">{{ dev.name }}</span>
              </div>
              <div v-if="filteredDevelopers.length === 0" class="text-sm text-muted-foreground text-center py-2">
                No developers found
              </div>
            </div>
          </div>

          <!-- Export Format -->
          <div class="space-y-3">
            <Label class="text-sm font-medium">Export Format</Label>
            <div class="flex gap-4">
              <label
                class="flex items-center gap-2 px-4 py-3 border rounded-lg cursor-pointer transition-all"
                :class="exportFormat === 'excel' ? 'border-primary bg-primary/5' : 'hover:bg-muted/50'"
              >
                <input
                  type="radio"
                  value="excel"
                  v-model="exportFormat"
                  class="accent-primary"
                />
                <div>
                  <div class="text-sm font-medium">Excel (.xlsx)</div>
                  <div class="text-xs text-muted-foreground">Best for data analysis</div>
                </div>
              </label>
              <label
                class="flex items-center gap-2 px-4 py-3 border rounded-lg cursor-pointer transition-all"
                :class="exportFormat === 'pdf' ? 'border-primary bg-primary/5' : 'hover:bg-muted/50'"
              >
                <input
                  type="radio"
                  value="pdf"
                  v-model="exportFormat"
                  class="accent-primary"
                />
                <div>
                  <div class="text-sm font-medium">PDF (.pdf)</div>
                  <div class="text-xs text-muted-foreground">Best for presentations</div>
                </div>
              </label>
            </div>
          </div>

          <!-- Additional Options -->
          <div class="space-y-3">
            <Label class="text-sm font-medium">Additional Options</Label>
            <div class="space-y-2">
              <label class="flex items-center gap-2 cursor-pointer">
                <Checkbox v-model:checked="includeCharts" />
                <span class="text-sm">Include charts and visualizations</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <Checkbox v-model:checked="includeSummary" />
                <span class="text-sm">Include summary statistics</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <Checkbox v-model:checked="groupByDeveloper" />
                <span class="text-sm">Group by developer</span>
              </label>
              <label v-if="exportFormat === 'excel'" class="flex items-center gap-2 cursor-pointer">
                <Checkbox v-model:checked="includeRawWakatime" />
                <span class="text-sm">Include raw WakaTime data</span>
              </label>
            </div>
          </div>

          <!-- Error Message -->
          <div v-if="exportError" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
            <p class="text-sm text-red-600 dark:text-red-400">{{ exportError }}</p>
          </div>
        </div>

        <DialogFooter class="gap-2">
          <DialogClose as-child>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button
            @click="handleExport"
            :disabled="!isFormValid || isExporting"
          >
            <Loader2 v-if="isExporting" class="mr-2 h-4 w-4 animate-spin" />
            {{ isExporting ? 'Generating...' : 'Export' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
