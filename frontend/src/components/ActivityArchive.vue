<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { API_BASE_URL } from '../config';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import DeveloperDayDetail from './DeveloperDayDetail.vue';

interface DailyMetric {
  developer: string;
  developer_id?: number;
  commits: number;
  coding_time: string;
  start?: string;
  end?: string;
  score: number;
}

interface DayArchive {
  date: string;
  items: DailyMetric[];
}

const archiveData = ref<DayArchive[]>([]);
const loading = ref(false);
const error = ref('');

// Detail modal state
const detailVisible = ref(false);
const selectedDeveloperId = ref<number | null>(null);
const selectedDeveloperName = ref('');
const selectedDate = ref('');

const fetchHistory = async () => {
  loading.value = true;
  error.value = '';
  try {
    const response = await fetch(`${API_BASE_URL}/metrics/?t=${Date.now()}`, {
      headers: { 'Cache-Control': 'no-cache' }
    });
    if (!response.ok) throw new Error(await response.text());
    archiveData.value = await response.json();
  } catch (err) {
    error.value = `Failed to load history: ${err}`;
  } finally {
    loading.value = false;
  }
};

const openDetail = (item: DailyMetric, date: string) => {
  if (!item.developer_id) return;
  selectedDeveloperId.value = item.developer_id;
  selectedDeveloperName.value = item.developer;
  selectedDate.value = date;
  detailVisible.value = true;
};

const formatDate = (dateStr: string) => {
  if (!dateStr) return '';
  const [year, month, day] = dateStr.split('-').map(Number);
  const date = new Date(year, month - 1, day);
  return date.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'numeric', day: 'numeric' });
};

// Timezone handling
const props = defineProps<{
  timezone?: string
}>();

const currentTimezone = computed(() => props.timezone || 'Asia/Tehran');

const formatTimeInZone = (timeStr: string | null) => {
  if (!timeStr) return '-';
  
  // Try to parse ISO string directly
  const date = new Date(timeStr);
  if (isNaN(date.getTime())) return timeStr;

  try {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
      timeZone: currentTimezone.value
    }).format(date);
  } catch (e) {
    console.error('Timezone error', e);
    return timeStr;
  }
};

onMounted(() => {
  fetchHistory();
});
</script>

<template>
  <Card class="mt-8">
    <CardHeader>
      <CardTitle class="flex justify-between items-center">
        <span>Activity Archive (Last 30 Days)</span>
      </CardTitle>
      <CardDescription>
        Click on any row to see detailed breakdown
      </CardDescription>
    </CardHeader>
    <CardContent>
      <div v-if="loading" class="text-center p-4">Loading history...</div>
      <div v-if="error" class="p-4 mb-4 text-red-700 bg-red-100 rounded">{{ error }}</div>
      
      <div v-if="!loading && archiveData.length === 0" class="text-center text-gray-500">
        No historical data found.
      </div>

      <div v-for="day in archiveData" :key="day.date" class="mb-6 border-b pb-4 last:border-0">
        <h3 class="text-lg font-semibold text-gray-700 mb-2">{{ formatDate(day.date) }}</h3>
        
        <div class="rounded-md border">
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>Developer</TableHead>
                        <TableHead>Commits</TableHead>
                        <TableHead>Start</TableHead>
                        <TableHead>End</TableHead>
                        <TableHead>Duration</TableHead>
                        <TableHead>Score</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    <TableRow 
                        v-for="item in day.items" 
                        :key="item.developer" 
                        class="cursor-pointer hover:bg-gray-50"
                        @click="openDetail(item, day.date)"
                    >
                        <TableCell class="font-medium">{{ item.developer }}</TableCell>
                        <TableCell>{{ item.commits }}</TableCell>
                        <TableCell>{{ formatTimeInZone(item.start ?? null) }}</TableCell>
                        <TableCell>{{ formatTimeInZone(item.end ?? null) }}</TableCell>
                        <TableCell>{{ item.coding_time }}</TableCell>
                        <TableCell>
                            <span class="font-bold" :class="item.score > 50 ? 'text-green-600' : item.score > 0 ? 'text-yellow-600' : 'text-gray-400'">
                                {{ item.score.toFixed(2) }}
                            </span>
                        </TableCell>
                    </TableRow>
                </TableBody>
            </Table>
        </div>
      </div>
    </CardContent>
  </Card>

  <!-- Detail Modal -->
  <DeveloperDayDetail
    v-model:visible="detailVisible"
    :developer-id="selectedDeveloperId"
    :developer-name="selectedDeveloperName"
    :date="selectedDate"
  />
</template>
