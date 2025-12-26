<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { API_BASE_URL } from '../config';
import AddDeveloperForm from './AddDeveloperForm.vue';
import RepositoryManager from './RepositoryManager.vue';
import TargetedSync from './TargetedSync.vue';
import ActivityArchive from './ActivityArchive.vue';
import Button from 'primevue/button';
import Card from 'primevue/card';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Message from 'primevue/message';
import Tag from 'primevue/tag';
import { Line } from 'vue-chartjs';
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
const expandedRows = ref([]);

// Chart configuration
const chartData = computed(() => ({
  labels: summary.value?.trend.labels.map(d => {
    const date = new Date(d);
    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  }) || [],
  datasets: [
    {
      label: 'Team Score',
      data: summary.value?.trend.scores || [],
      borderColor: 'rgb(99, 102, 241)',
      backgroundColor: 'rgba(99, 102, 241, 0.1)',
      fill: true,
      tension: 0.4
    },
    {
      label: 'Commits',
      data: summary.value?.trend.commits || [],
      borderColor: 'rgb(34, 197, 94)',
      backgroundColor: 'rgba(34, 197, 94, 0.1)',
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
    },
    title: {
      display: false
    }
  },
  scales: {
    y: {
      beginAtZero: true
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
    const response = await fetch(`${API_BASE_URL}/metrics/summary?days=7`);
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
    const response = await fetch(`${API_BASE_URL}/sync`, { method: 'POST' });
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
    const response = await fetch(`${API_BASE_URL}/metrics/?days=7`);
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
  // Only fetch existing data on load - NO auto-sync
  fetchExistingMetrics();
  fetchSummary();
});
</script>

<template>
  <div class="max-w-7xl mx-auto p-4">
    <h1 class="text-3xl font-bold text-center mb-8 text-gray-900">
      Performance Optimizer
    </h1>

    <!-- Stats Cards Row -->
    <div v-if="summary" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <Card class="text-center">
        <template #content>
          <div class="text-3xl font-bold text-indigo-600">{{ summary.totals.total_score.toFixed(0) }}</div>
          <div class="text-sm text-gray-500 mt-1">Total Score (7d)</div>
        </template>
      </Card>
      <Card class="text-center">
        <template #content>
          <div class="text-3xl font-bold text-green-600">{{ summary.totals.total_commits }}</div>
          <div class="text-sm text-gray-500 mt-1">Total Commits</div>
        </template>
      </Card>
      <Card class="text-center">
        <template #content>
          <div class="text-3xl font-bold text-blue-600">{{ summary.totals.active_developers }}</div>
          <div class="text-sm text-gray-500 mt-1">Active Developers</div>
        </template>
      </Card>
      <Card class="text-center">
        <template #content>
          <div class="text-3xl font-bold text-purple-600">{{ summary.totals.days_tracked }}</div>
          <div class="text-sm text-gray-500 mt-1">Days Tracked</div>
        </template>
      </Card>
    </div>

    <!-- Performance Trend Chart -->
    <Card v-if="summary && summary.trend.labels.length > 0" class="mb-6">
      <template #title>
        <span class="text-lg">Performance Trend (Last 7 Days)</span>
      </template>
      <template #content>
        <div style="height: 250px;">
          <Line :data="chartData" :options="chartOptions" />
        </div>
      </template>
    </Card>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="md:col-span-1 flex flex-col gap-6">
        <RepositoryManager />
        <AddDeveloperForm @developerDataChanged="syncData" />
        
        <!-- Leaderboard Card -->
        <Card v-if="summary && summary.leaderboard.length > 0">
          <template #title>Top Performers</template>
          <template #content>
            <div class="space-y-2">
              <div v-for="(dev, idx) in summary.leaderboard.slice(0, 5)" :key="dev.name" 
                   class="flex items-center justify-between p-2 rounded" 
                   :class="idx === 0 ? 'bg-yellow-50' : 'bg-gray-50'">
                <div class="flex items-center gap-2">
                  <span class="font-bold text-gray-400 w-4">{{ idx + 1 }}</span>
                  <span class="font-medium">{{ dev.name }}</span>
                </div>
                <Tag :value="dev.total_score.toFixed(0)" :severity="idx === 0 ? 'success' : 'info'" />
              </div>
            </div>
          </template>
        </Card>
      </div>

      <div class="md:col-span-2 flex flex-col gap-6">
        <Card>
            <template #title>
                <div class="flex justify-between items-center">
                    <span>Contribution Board</span>
                    <div class="flex gap-2">
                         <Button @click="syncData" :loading="loading" label="Sync Data" icon="pi pi-refresh" size="small" />
                         <TargetedSync />
                    </div>
                </div>
            </template>
            <template #content>
                 <div v-if="syncMessage" class="mb-4">
                     <Message :severity="syncMessage.includes('failed') || syncMessage.includes('error') ? 'error' : 'success'" :closable="false">{{ syncMessage }}</Message>
                 </div>

                 <DataTable v-model:expandedRows="expandedRows" :value="metrics" dataKey="developer" tableStyle="min-width: 50rem">
                    <Column expander style="width: 3rem" />
                    <Column field="developer" header="Developer"></Column>
                    <Column field="commits" header="Commits" sortable></Column>
                    <Column header="Time" sortable field="coding_time">
                        <template #body="slotProps">
                            {{ slotProps.data.coding_time }}
                            <div v-if="slotProps.data.deep_work" class="text-xs text-gray-500">
                                Deep Work: {{ slotProps.data.deep_work }}
                            </div>
                        </template>
                    </Column>
                    <Column field="start" header="Start" sortable>
                        <template #body="slotProps">
                            {{ slotProps.data.start || '-' }}
                        </template>
                    </Column>
                    <Column field="end" header="End" sortable>
                        <template #body="slotProps">
                            {{ slotProps.data.end || '-' }}
                        </template>
                    </Column>
                    <Column field="score" header="Score" sortable>
                        <template #body="slotProps">
                            <Tag :value="slotProps.data.score.toFixed(2)" :severity="slotProps.data.score > 50 ? 'success' : 'warning'" />
                        </template>
                    </Column>

                    <template #expansion="slotProps">
                        <div class="p-4 bg-gray-50">
                            <h4 class="font-bold mb-2">Detailed Productivity Analysis</h4>
                             <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <p><strong>Focus Rate:</strong> {{ (slotProps.data.focus_ratio * 100).toFixed(0) }}%</p>
                                    <p><strong>Context Switches:</strong> {{ slotProps.data.switches }}</p>
                                </div>
                                <div v-if="slotProps.data.details">
                                    <h5 class="text-sm font-semibold mt-2">Top Languages:</h5>
                                    <ul class="list-disc pl-5 text-sm">
                                        <li v-for="lang in getLanguages(slotProps.data.details).slice(0, 3)" :key="lang.name">
                                            {{ lang.name }}: {{ lang.text }} ({{ lang.percent }}%)
                                        </li>
                                    </ul>
                                </div>
                            </div>
                            <!-- Projects Section -->
                             <div v-if="slotProps.data.details" class="mt-2">
                                <h5 class="text-sm font-semibold mt-2">Projects:</h5>
                                <div class="flex flex-wrap gap-2">
                                    <Tag v-for="proj in getProjects(slotProps.data.details)" :key="proj.name" severity="info" :value="proj.name + ': ' + proj.text" />
                                </div>
                             </div>
                        </div>
                    </template>
                 </DataTable>
            </template>
        </Card>

        <ActivityArchive />
      </div>
    </div>
  </div>
</template>
