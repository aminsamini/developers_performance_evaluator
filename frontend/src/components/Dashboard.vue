<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { RefreshCw } from 'lucide-vue-next';
import { cn } from '@/lib/utils';
import { API_BASE_URL } from '../config';
import RepositoryManager from './RepositoryManager.vue';
import TargetedSync from './TargetedSync.vue';
import ActivityArchive from './ActivityArchive.vue';
import TimezoneSelector from './TimezoneSelector.vue';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { ChevronDown, ChevronRight, ChevronUp } from 'lucide-vue-next';
import ThemeToggle from './ThemeToggle.vue';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'vue-chartjs';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

interface MetricResult {
  developer: string;
  developer_id?: number;
  commits: number;
  coding_time: string;
  score: number;
  start?: string;
  end?: string;
  deep_work?: string;
  focus_ratio?: number;
  switches?: number;
  details?: string;
}

interface SummaryData {
  trend: {
    labels: string[];
    scores: number[];
    commits: number[];
  };
  leaderboard: { name: string; total_score: number; total_commits: number; avg_score: number; days_active: number }[];
  totals: {
    total_score: number;
    total_commits: number;
    active_developers: number;
    days_tracked: number;
  };
}

const metrics = ref<MetricResult[]>([]);
const summary = ref<SummaryData | null>(null);
const loading = ref(false);
const syncMessage = ref('');
const selectedTimezone = ref('Asia/Tehran'); // Default timezone

// Enhanced Table State
const expandedRows = ref<Set<string>>(new Set());
const sortKey = ref('score');
const sortOrder = ref<'asc' | 'desc'>('desc');

const toggleExpansion = (developerName: string) => {
  if (expandedRows.value.has(developerName)) {
    expandedRows.value.delete(developerName);
  } else {
    expandedRows.value.add(developerName);
  }
};

const handleSort = (key: string) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'desc';
  }
};

const sortedMetrics = computed(() => {
  return [...metrics.value].sort((a: any, b: any) => {
    const aVal = a[sortKey.value];
    const bVal = b[sortKey.value];
    if (aVal === bVal) return 0;
    const modifier = sortOrder.value === 'asc' ? 1 : -1;
    // Handle strings
    if (typeof aVal === 'string' && typeof bVal === 'string') {
        return aVal.localeCompare(bVal) * modifier;
    }
    return (aVal > bVal ? 1 : -1) * modifier;
  });
});

// Chart configuration
const chartData = computed(() => ({
  labels: summary.value?.trend.labels.map(d => {
    // Parse YYYY-MM-DD manually to avoid timezone shift
    if (!d) return '';
    const [year, month, day] = d.split('-').map(Number);
    const date = new Date(year, month - 1, day);
    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  }) || [],
  datasets: [
    {
      label: 'Team Score',
      data: summary.value?.trend.scores || [],
      borderColor: 'hsl(var(--foreground))',
      backgroundColor: 'hsl(var(--foreground) / 0.1)',
      fill: true,
      tension: 0.4
    },
    {
      label: 'Commits',
      data: summary.value?.trend.commits || [],
      borderColor: 'hsl(var(--muted-foreground))',
      backgroundColor: 'hsl(var(--muted-foreground) / 0.1)',
      fill: true,
      tension: 0.4
    }
  ]
}));

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
      labels: {
        color: 'hsl(var(--muted-foreground))'
      }
    },
    title: {
      display: false
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: {
        color: 'hsl(var(--border))'
      },
      ticks: {
        color: 'hsl(var(--muted-foreground))'
      }
    },
    x: {
      grid: {
        color: 'hsl(var(--border))'
      },
      ticks: {
        color: 'hsl(var(--muted-foreground))'
      }
    }
  }
};

const getLanguages = (jsonStr: string) => {
  try {
    const data = JSON.parse(jsonStr);
    return data.languages || [];
  } catch (e) {
    return [];
  }
};

const getProjects = (jsonStr: string) => {
    try {
        const data = JSON.parse(jsonStr);
        return data.projects || [];
    } catch (e) {
        return [];
    }
};

const fetchSummary = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/metrics/summary?days=7&t=${Date.now()}`, {
      headers: { 'Cache-Control': 'no-cache' }
    });
    if (response.ok) {
      summary.value = await response.json();
    }
  } catch (error) {
    console.error('Failed to fetch summary:', error);
  }
};

// Manual sync button - ADDITIVE: only syncs days without existing data
const syncData = async () => {
  loading.value = true;
  syncMessage.value = 'Syncing new data...';
  try {
    const response = await fetch(`${API_BASE_URL}/sync?t=${Date.now()}`, { 
      method: 'POST',
      headers: { 'Cache-Control': 'no-cache' } 
    });
    if (response.ok) {
      const data = await response.json();
      if (data.results && data.results.length > 0) {
        // Merge new results with existing
        metrics.value = data.results;
        syncMessage.value = `Synced ${data.results.length} new records!`;
      } else {
        syncMessage.value = 'All data is already up to date.';
      }
      await fetchSummary();
      await fetchExistingMetrics();
    } else {
      const errText = await response.text();
      syncMessage.value = `Sync failed: ${errText}`;
    }
  } catch (error) {
    syncMessage.value = `Network error: ${error}`;
  } finally {
    loading.value = false;
  }
};

// Fetch existing metrics from database (no sync)
const fetchExistingMetrics = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/metrics/?days=7&t=${Date.now()}`, {
      headers: { 'Cache-Control': 'no-cache' }
    });
    if (response.ok) {
      const data = await response.json();
      // Flatten the grouped data for display
      if (data.length > 0) {
        metrics.value = data[0].items || [];
      }
    }
  } catch (error) {
    console.error('Failed to fetch metrics:', error);
  }
};

onMounted(() => {
  fetchExistingMetrics();
  fetchSummary();
});

const formatTimeInZone = (timeStr: string | null) => {
  if (!timeStr) return '-';
  const date = new Date(timeStr);
  if (isNaN(date.getTime())) return timeStr;

  try {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
      timeZone: selectedTimezone.value
    }).format(date);
  } catch (e) {
    return timeStr;
  }
};

const refreshView = async () => {
  await fetchSummary();
  await fetchExistingMetrics();
};
</script>

<template>
  <div class="max-w-7xl mx-auto p-4">
    <div class="flex justify-between items-center mb-8">
      <h1 class="text-3xl font-bold text-foreground">
        Performance Optimizer
      </h1>
      <div class="flex items-center gap-2">
         <ThemeToggle />
         <TimezoneSelector @update:timezone="(tz: string) => selectedTimezone = tz" />
      </div>
    </div>

    <!-- Stats Cards Row -->
    <div v-if="summary" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <Card class="text-center">
        <CardContent class="pt-6">
          <div class="text-3xl font-bold text-primary">{{ summary.totals.total_score.toFixed(0) }}</div>
          <div class="text-sm text-muted-foreground mt-1">Total Score (7d)</div>
        </CardContent>
      </Card>
      <Card class="text-center">
        <CardContent class="pt-6">
          <div class="text-3xl font-bold text-primary">{{ summary.totals.total_commits }}</div>
          <div class="text-sm text-muted-foreground mt-1">Total Commits</div>
        </CardContent>
      </Card>
      <Card class="text-center">
        <CardContent class="pt-6">
          <div class="text-3xl font-bold text-primary">{{ summary.totals.active_developers }}</div>
          <div class="text-sm text-muted-foreground mt-1">Active Developers</div>
        </CardContent>
      </Card>
      <Card class="text-center">
        <CardContent class="pt-6">
          <div class="text-3xl font-bold text-primary">{{ summary.totals.days_tracked }}</div>
          <div class="text-sm text-muted-foreground mt-1">Days Tracked</div>
        </CardContent>
      </Card>
    </div>

    <ActivityArchive :timezone="selectedTimezone" />

    <!-- Performance Trend Chart -->
    <Card v-if="summary && summary.trend.labels.length > 0" class="mb-6">
      <CardHeader>
        <CardTitle>Performance Trend (Last 7 Days)</CardTitle>
      </CardHeader>
      <CardContent>
        <div style="height: 250px;">
          <Line :data="chartData" :options="chartOptions" />
        </div>
      </CardContent>
    </Card>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="md:col-span-1 flex flex-col gap-6">
        <!-- Leaderboard Card -->
        <Card v-if="summary && summary.leaderboard.length > 0">
          <CardHeader>
            <CardTitle>Top Performers</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="space-y-2">
              <div v-for="(dev, idx) in summary.leaderboard.slice(0, 5)" :key="dev.name" 
                   class="flex items-center justify-between p-2 rounded" 
                   :class="idx === 0 ? 'bg-primary/10 border border-primary/20' : 'bg-muted/50'">
                <div class="flex items-center gap-2">
                  <div class="font-bold w-6 h-6 flex items-center justify-center rounded-full text-xs"
                       :class="idx === 0 ? 'bg-primary text-primary-foreground' : 'text-muted-foreground bg-muted'">
                       {{ idx + 1 }}
                  </div>
                  <div class="flex flex-col">
                      <span class="font-medium text-sm">{{ dev.name }}</span>
                      <span class="text-xs text-muted-foreground" v-if="idx===0">Top Performer</span>
                  </div>
                </div>
                <!-- Keeping PrimeVue Tag for now, or migrate to Badge later -->
                <Badge :variant="idx === 0 ? 'default' : 'secondary'">{{ dev.total_score.toFixed(0) }} pts</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <RepositoryManager @dataUpdated="syncData" />
      </div>

      <div class="md:col-span-2 flex flex-col gap-6">
        <Card>
            <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle>Contribution Board</CardTitle>
                <div class="flex gap-2">
                     <Button variant="outline" size="sm" @click="syncData" :disabled="loading">
                        <RefreshCw class="mr-2 h-4 w-4" :class="{ 'animate-spin': loading }" />
                        Sync Data
                     </Button>
                     <TargetedSync @dataUpdated="refreshView" />
                </div>
            </CardHeader>
            <CardContent>
                 <div v-if="syncMessage" class="mb-4">
                     <Message :severity="syncMessage.includes('failed') || syncMessage.includes('error') ? 'error' : 'success'" :closable="false">{{ syncMessage }}</Message>
                 </div>

                 <div class="rounded-md border">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead class="w-[50px]"></TableHead>
                                <TableHead @click="handleSort('developer')" class="cursor-pointer hover:bg-gray-100 font-bold">
                                    Developer 
                                    <ChevronDown v-if="sortKey === 'developer' && sortOrder === 'desc'" class="inline h-4 w-4 ml-1" />
                                    <ChevronUp v-if="sortKey === 'developer' && sortOrder === 'asc'" class="inline h-4 w-4 ml-1" />
                                </TableHead>
                                <TableHead @click="handleSort('commits')" class="cursor-pointer hover:bg-gray-100 font-bold">
                                    Commits
                                    <ChevronDown v-if="sortKey === 'commits' && sortOrder === 'desc'" class="inline h-4 w-4 ml-1" />
                                    <ChevronUp v-if="sortKey === 'commits' && sortOrder === 'asc'" class="inline h-4 w-4 ml-1" />
                                </TableHead>
                                <TableHead @click="handleSort('coding_time')" class="cursor-pointer hover:bg-gray-100 font-bold">
                                    Time
                                    <ChevronDown v-if="sortKey === 'coding_time' && sortOrder === 'desc'" class="inline h-4 w-4 ml-1" />
                                    <ChevronUp v-if="sortKey === 'coding_time' && sortOrder === 'asc'" class="inline h-4 w-4 ml-1" />
                                </TableHead>
                                <TableHead @click="handleSort('start')" class="cursor-pointer hover:bg-gray-100 font-bold">
                                    Start
                                    <ChevronDown v-if="sortKey === 'start' && sortOrder === 'desc'" class="inline h-4 w-4 ml-1" />
                                    <ChevronUp v-if="sortKey === 'start' && sortOrder === 'asc'" class="inline h-4 w-4 ml-1" />
                                </TableHead>
                                <TableHead @click="handleSort('end')" class="cursor-pointer hover:bg-gray-100 font-bold">
                                    End
                                    <ChevronDown v-if="sortKey === 'end' && sortOrder === 'desc'" class="inline h-4 w-4 ml-1" />
                                    <ChevronUp v-if="sortKey === 'end' && sortOrder === 'asc'" class="inline h-4 w-4 ml-1" />
                                </TableHead>
                                <TableHead @click="handleSort('score')" class="cursor-pointer hover:bg-gray-100 font-bold">
                                    Score
                                    <ChevronDown v-if="sortKey === 'score' && sortOrder === 'desc'" class="inline h-4 w-4 ml-1" />
                                    <ChevronUp v-if="sortKey === 'score' && sortOrder === 'asc'" class="inline h-4 w-4 ml-1" />
                                </TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            <template v-for="metric in sortedMetrics" :key="metric.developer">
                                <TableRow>
                                    <TableCell>
                                        <Button variant="ghost" size="sm" @click="toggleExpansion(metric.developer)">
                                            <component :is="expandedRows.has(metric.developer) ? ChevronDown : ChevronRight" class="h-4 w-4" />
                                        </Button>
                                    </TableCell>
                                    <TableCell class="font-medium">{{ metric.developer }}</TableCell>
                                    <TableCell>{{ metric.commits }}</TableCell>
                                    <TableCell>
                                        {{ metric.coding_time }}
                                        <div v-if="metric.deep_work" class="text-xs text-gray-500">
                                            Deep Work: {{ metric.deep_work }}
                                        </div>
                                    </TableCell>
                                    <TableCell>{{ formatTimeInZone(metric.start) }}</TableCell>
                                    <TableCell>{{ formatTimeInZone(metric.end) }}</TableCell>
                                    <TableCell>
                                        <Badge :variant="metric.score > 50 ? 'default' : 'secondary'">{{ metric.score.toFixed(2) }}</Badge>
                                    </TableCell>
                                </TableRow>
                                <TableRow v-if="expandedRows.has(metric.developer)">
                                    <TableCell colspan="7" class="bg-gray-50/50 p-4">
                                        <div class="p-4 bg-white rounded shadow-sm border">
                                            <h4 class="font-bold mb-2">Detailed Productivity Analysis</h4>
                                            <div class="grid grid-cols-2 gap-4">
                                                <div>
                                                    <p class="text-sm"><strong>Focus Rate:</strong> {{ ((metric.focus_ratio || 0) * 100).toFixed(0) }}%</p>
                                                    <p class="text-sm"><strong>Context Switches:</strong> {{ metric.switches }}</p>
                                                </div>
                                                <div v-if="metric.details">
                                                    <h5 class="text-sm font-semibold mt-2">Top Languages:</h5>
                                                    <ul class="list-disc pl-5 text-sm">
                                                        <li v-for="lang in getLanguages(metric.details).slice(0, 3)" :key="lang.name">
                                                            {{ lang.name }}: {{ lang.text }} ({{ lang.percent }}%)
                                                        </li>
                                                    </ul>
                                                </div>
                                            </div>
                                            <!-- Projects Section -->
                                            <div v-if="metric.details" class="mt-2">
                                                <h5 class="text-sm font-semibold mt-2">Projects:</h5>
                                                <div class="flex flex-wrap gap-2">
                                                     <Badge v-for="proj in getProjects(metric.details)" :key="proj.name" variant="outline">{{ proj.name }}: {{ proj.text }}</Badge>
                                                </div>
                                            </div>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            </template>
                        </TableBody>
                    </Table>
                 </div>
            </CardContent>
        </Card>

        <ActivityArchive :timezone="selectedTimezone" />
      </div>
    </div>
  </div>
</template>
