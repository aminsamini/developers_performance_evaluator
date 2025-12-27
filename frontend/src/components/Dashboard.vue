<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { 
  RefreshCw, 
  TrendingUp, 
  ChevronDown, 
  ChevronRight, 
  ChevronUp,
  Activity,
  GitCommit,
  Clock,
  Archive
} from 'lucide-vue-next';
import { cn } from '@/lib/utils';
import { API_BASE_URL } from '../config';
import RepositoryManager from './RepositoryManager.vue';
import TargetedSync from './TargetedSync.vue';
import ActivityArchive from './ActivityArchive.vue';
import TimezoneSelector from './TimezoneSelector.vue';
import ThemeToggle from './ThemeToggle.vue';
import ExportModal from './ExportModal.vue';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

// Chart.js Imports
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  RadialLinearScale,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  LineController,
  PolarAreaController,
  RadarController,
  DoughnutController
} from 'chart.js';
import { Line, Doughnut, Radar } from 'vue-chartjs';

// Register Chart.js components manually including Controllers
ChartJS.register(
    CategoryScale, 
    LinearScale, 
    PointElement, 
    LineElement, 
    RadialLinearScale, 
    ArcElement, 
    Title, 
    Tooltip, 
    Legend, 
    Filler,
    LineController,
    PolarAreaController,
    RadarController,
    DoughnutController
);

// ...



// ...



// ...

// In Template (Change PolarArea to Doughnut)
// ...
// <Doughnut :data="radialData" :options="radialOptions" />
// ...

interface MetricResult {
  developer: string;
  developer_id?: number;
  commits: number;
  lines_added?: number;
  lines_deleted?: number;
  coding_time: string;
  start?: string;
  end?: string;
  score: number;
  details?: string;
}

interface TrendResult {
  labels: string[];
  scores: number[];
  commits: number[];
}

interface SummaryStats {
  trend: TrendResult;
  leaderboard: {
    name: string;
    total_score: number;
    total_commits: number;
    avg_score: number;
    days_active: number;
  }[];
  totals: {
    commits: number;
    active_developers: number;
    repos: number;
    score: number;
  };
}

const summary = ref<SummaryStats | null>(null);
const metrics = ref<MetricResult[]>([]);
const lastSync = ref<string>('');
const selectedTimezone = ref('Asia/Tehran');
const error = ref('');
const developers = ref<{id: number, name: string}[]>([]);

// Fetch Data
const fetchExampleData = async () => {
    // Fallback or Initial Data
};

const fetchSummary = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/metrics/summary`);
    if (!response.ok) throw new Error('Failed to fetch summary');
    summary.value = await response.json();
  } catch (err) {
    console.error('Error fetching summary:', err);
    error.value = 'Failed to load dashboard data.';
  }
};

const fetchExistingMetrics = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/metrics/`);
    if (!response.ok) throw new Error('Failed to fetch metrics');
    const result = await response.json();
    // Handle new paginated response format
    const data = result.data || result;
    if (data && data.length > 0) {
       // Flatten all days items to support historical aggregation
       metrics.value = data.flatMap((day: any) => day.items || []);
    }
  } catch (err) {
    console.error('Error fetching metrics:', err);
  }
};

const syncData = async () => {
    await fetchSummary();
    await fetchExistingMetrics();
    lastSync.value = new Date().toLocaleTimeString();
};

const fetchDevelopers = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/developers/`);
    if (response.ok) {
      developers.value = await response.json();
    }
  } catch (err) {
    console.error('Error fetching developers:', err);
  }
};

onMounted(() => {
  syncData();
  fetchDevelopers();
});

// Chart Logic
const selectedChart = ref<string | null>(null);

const selectedChartTitle = computed(() => {
    switch (selectedChart.value) {
        case 'trend': return 'Performance Trend Analysis';
        case 'distribution': return 'Activity & Language Distribution';
        case 'health': return 'Team Health Radar';
        default: return 'Chart Details';
    }
});

// 1. Line Chart Data (Trend)
const chartData = computed(() => ({
  labels: summary.value?.trend.labels || [],
  datasets: [
    {
      label: 'Performance Score',
      data: summary.value?.trend.scores || [],
      borderColor: '#3b82f6', // blue-500
      backgroundColor: (context: any) => {
        const ctx = context.chart.ctx;
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.5)'); // blue-500
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)');
        return gradient;
      },
      tension: 0.4,
      fill: true,
      pointRadius: 4,
      pointHoverRadius: 6,
    }
  ],
}));

// 2. Radial Data (Aggregated KPI Metrics - 6 Rings)
const radialData = computed(() => {
  if (metrics.value.length === 0) {
     return { labels: ['No Data'], datasets: [{ data: [1], backgroundColor: ['#e2e8f0'] }] };
  }
  
  const records = metrics.value;
  const totalRecs = records.length;

  // 1. Coding Hours Average (Target 8h)
  const totalCodingSec = records.reduce((sum, r) => {
      const d = r.details ? JSON.parse(r.details) : {};
      return sum + (d.grand_total?.total_seconds || 0);
  }, 0);
  const avgCodingHrs = (totalCodingSec / totalRecs) / 3600;
  const codingPercent = Math.min((avgCodingHrs / 8) * 100, 100);

  // 2. Focus Average (Avg of Daily Top Project %)
  const focusSum = records.reduce((sum, r) => {
      const d = r.details ? JSON.parse(r.details) : {};
      const total = d.grand_total?.total_seconds || 0;
      if (total === 0 || !d.projects) return sum;
      
      let maxP = 0;
      (d.projects || []).forEach((p: any) => {
          const pSec = p.total_seconds || (p.percent ? (p.percent/100 * total) : 0);
          if (pSec > maxP) maxP = pSec;
      });
      return sum + ((maxP / total) * 100);
  }, 0);
  const avgFocus = focusSum / totalRecs;

  // 3. Score Average (0-100)
  const avgScore = records.reduce((sum, r) => sum + (r.score || 0), 0) / totalRecs;

  // 4. Commit Consistency (% of days with > 0 commits)
  const commitDays = records.filter(r => r.commits > 0).length;
  const commitConsistency = (commitDays / totalRecs) * 100;

  // 5. Code Quality (1 - Churn). Churn = DELETIONS / (ADDS + DELS). 
  // If (add+del) == 0, is Quality 100%? Yes per user spec.
  const qualitySum = records.reduce((sum, r) => {
      const adds = r.lines_added || 0;
      const dels = r.lines_deleted || 0;
      const total = adds + dels;
      if (total === 0) return sum + 100; // Perfect stability if no churn? Or ignore? User says 100.
      const churn = dels / total;
      return sum + ((1 - churn) * 100);
  }, 0);
  const avgQuality = qualitySum / totalRecs;

  // 6. Active Days (% days with Coding > 0)
  const activeCount = records.filter(r => {
      const d = r.details ? JSON.parse(r.details) : {};
      return (d.grand_total?.total_seconds || 0) > 0;
  }).length;
  const activeDaysPercent = (activeCount / totalRecs) * 100;

  const chartColors = [
      '#93c5fd', // Coding (Blue 300)
      '#3b82f6', // Focus (Blue 500)
      '#2563eb', // Score (Blue 600)
      '#1d4ed8', // Consistency (Blue 700)
      '#1e40af', // Quality (Blue 800)
      '#1e3a8a', // Active (Blue 900)
  ];

  const ringData = [
      { label: `${avgCodingHrs.toFixed(1)}h avg`, val: codingPercent },
      { label: `${avgFocus.toFixed(0)}% avg focus`, val: avgFocus },
      { label: `${avgScore.toFixed(1)} avg score`, val: avgScore },
      { label: `${commitDays}/${totalRecs} days`, val: commitConsistency },
      { label: `${avgQuality.toFixed(0)}% quality`, val: avgQuality },
      { label: `${activeCount}/${totalRecs} active`, val: activeDaysPercent }
  ];

  return {
      labels: ringData.map(r => r.label),
      datasets: ringData.map((r, i) => ({
          label: r.label,
          data: [r.val, 100 - r.val],
          backgroundColor: [chartColors[i], 'transparent'],
          borderWidth: 0,
          circumference: 360,
          rotation: -90,
          borderRadius: 5,
          weight: 1
      }))
  };
});

// 3. Radar Data (Health)
const radarData = computed(() => {
    // Mock data based on summary stats if real "health" metrics aren't broken down
    const score = summary.value?.totals.score ? Math.min(summary.value.totals.score / 100, 100) : 75;
    const activity = summary.value?.totals.active_developers ? (summary.value.totals.active_developers * 10) : 60;
    
    return {
        labels: ['Speed', 'Quality', 'Consistency', 'Collaboration', 'Impact'],
        datasets: [{
            label: 'Team Metrics',
            data: [activity, score, 85, 70, 90], // Mixed mock/real
            backgroundColor: 'rgba(59, 130, 246, 0.2)', // blue-500 @ 20%
            borderColor: '#3b82f6', // blue-500
            pointBackgroundColor: '#3b82f6',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: '#3b82f6',
            fill: true
        }]
    };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: { 
        mode: 'index' as const,
        intersect: false,
    }
  },
  scales: {
    y: { display: false },
    x: { display: false }
  }
};

const radialOptions = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '40%', // Size of center hole
    plugins: {
        legend: { display: false },
        tooltip: {
            enabled: true,
            filter: (item: any) => item.dataIndex === 0 // Show tooltip only for the value segment
        }
    }
};

const radarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
        r: {
            suggestedMin: 0,
            suggestedMax: 100,
            ticks: { display: false },
            grid: { color: 'rgba(0,0,0,0.1)' }
        }
    }
};

</script>

<template>
  <div class="max-w-7xl mx-auto p-4 md:p-8 space-y-8">
    <!-- Header -->
    <div class="flex flex-col md:flex-row justify-between items-center gap-4">
      <div>
        <h1 class="text-3xl font-bold tracking-tight text-foreground">Performance Optimizer</h1>
        <p class="text-muted-foreground">Team metrics, trends, and health analysis.</p>
      </div>
      <div class="flex items-center gap-2">
         <ExportModal :developers="developers" />
         <ThemeToggle class="z-50 relative" />
         <TimezoneSelector @update:timezone="(tz: string) => selectedTimezone = tz" />
         <TargetedSync />
         <Button @click="syncData" variant="outline" size="sm">
            <RefreshCw class="mr-2 h-4 w-4" :class="{ 'animate-spin': !summary }" />
            Sync
         </Button>
      </div>
    </div>

    <!-- Summary Stats Row -->
    <div v-if="summary" class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Total Commits</CardTitle>
          <GitCommit class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{{ summary.totals.commits ?? summary.totals.total_commits ?? 0 }}</div>
          <p class="text-xs text-muted-foreground">Across all repos</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Active Developers</CardTitle>
          <Activity class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{{ summary.totals.active_developers ?? summary.totals.developers ?? 0 }}</div>
          <p class="text-xs text-muted-foreground">Contributing this week</p>
        </CardContent>
      </Card>
       <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Tracked Repos</CardTitle>
          <Archive class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{{ summary.totals.repo_count ?? summary.totals.repos ?? 0 }}</div>
          <p class="text-xs text-muted-foreground">Active repositories</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Overall Score</CardTitle>
          <TrendingUp class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{{ typeof summary.totals.total_score === 'number' ? summary.totals.total_score.toFixed(1) : (summary.totals.score || 0).toFixed(1) }}</div>
          <p class="text-xs text-muted-foreground">Team performance index</p>
        </CardContent>
      </Card>
    </div>
    
    <!-- Charts Grid -->
    <div v-if="summary" class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- 1. Performace Trend -->
        <Card class="flex flex-col cursor-pointer transition-all hover:shadow-lg hover:border-primary/50" @click="selectedChart = 'trend'">
            <CardHeader class="pb-2">
                <CardTitle>Performance Trend</CardTitle>
                <div class="text-sm text-muted-foreground">Last 7 Days</div>
            </CardHeader>
            <CardContent class="pb-2">
                <div class="h-[250px] w-full">
                    <Line :data="chartData" :options="chartOptions" />
                </div>
            </CardContent>
            <div class="p-6 pt-0 flex w-full items-start gap-2 text-sm mt-auto">
                <div class="grid gap-2">
                    <div class="flex items-center gap-2 leading-none font-medium text-green-600">
                      Trending up by 5.2% <TrendingUp class="h-4 w-4" />
                    </div>
                </div>
            </div>
        </Card>

        <!-- 2. Activity Distribution -->
        <Card class="flex flex-col cursor-pointer transition-all hover:shadow-lg hover:border-primary/50" @click="selectedChart = 'distribution'">
            <CardHeader class="pb-2">
                <CardTitle>Activity Distribution</CardTitle>
                <div class="text-sm text-muted-foreground">Language & Work Type</div>
            </CardHeader>
            <CardContent class="pb-2">
                <div class="h-[250px] w-full">
                    <Doughnut :data="radialData" :options="radialOptions" />
                </div>
            </CardContent>
            <div class="p-6 pt-0 flex w-full items-start gap-2 text-sm mt-auto">
                <div class="grid gap-2">
                    <div class="flex items-center gap-2 leading-none font-medium">
                    Diversity Score: 8.5 <Activity class="h-4 w-4 text-blue-500" />
                    </div>
                </div>
            </div>
        </Card>

        <!-- 3. Team Health -->
        <Card class="flex flex-col cursor-pointer transition-all hover:shadow-lg hover:border-primary/50" @click="selectedChart = 'health'">
            <CardHeader class="pb-2">
                <CardTitle>Team Health Radar</CardTitle>
                <div class="text-sm text-muted-foreground">Skills & Metrics Analysis</div>
            </CardHeader>
            <CardContent class="pb-2">
                <div class="h-[250px] w-full">
                    <Radar :data="radarData" :options="radarOptions" />
                </div>
            </CardContent>
            <div class="p-6 pt-0 flex w-full items-start gap-2 text-sm mt-auto">
                <div class="grid gap-2">
                    <div class="flex items-center gap-2 leading-none font-medium text-indigo-600">
                    Overall Health: 92% <TrendingUp class="h-4 w-4" />
                    </div>
                </div>
            </div>
        </Card>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      
      <!-- Leaderboard Column -->
      <div class="md:col-span-1 flex flex-col gap-6">
        <Card v-if="summary">
          <CardHeader>
            <CardTitle>Top Performers</CardTitle>
            <CardDescription>Based on recent contributions</CardDescription>
          </CardHeader>
          <CardContent>
             <div class="space-y-4">
               <div v-for="(dev, idx) in summary.leaderboard" :key="dev.name" class="flex items-center justify-between p-3 rounded-lg bg-muted/50 border">
                  <div class="flex items-center gap-3">
                     <div class="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-bold text-sm">
                        {{ idx + 1 }}
                     </div>
                     <div class="grid gap-0.5">
                        <span class="font-medium text-sm">{{ dev.name }}</span>
                        <span class="text-xs text-muted-foreground">{{ idx === 0 ? 'Top Performer' : 'Contributor' }}</span>
                     </div>
                  </div>
                  <div class="text-right">
                    <span class="block font-bold text-sm">{{ dev.total_score.toLocaleString() }} pts</span>
                  </div>
               </div>
             </div>
          </CardContent>
        </Card>

        <RepositoryManager @dataUpdated="syncData" />
      </div>

      <!-- Activity Column -->
      <div class="md:col-span-2 flex flex-col gap-6">
        <ActivityArchive :timezone="selectedTimezone" />
      </div>
    </div>

    <!-- Chart Modal (Teleported via Dialog) -->
    <!-- We place it here; Shadcn Dialog renders to body usually -->
    <Dialog :open="!!selectedChart" @update:open="(val) => !val && (selectedChart = null)">
      <DialogContent class="max-w-4xl w-full h-[80vh] flex flex-col z-[100]" style="z-index: 100;">
        <DialogHeader>
          <DialogTitle>{{ selectedChartTitle }}</DialogTitle>
          <DialogDescription>Detailed breakdown of metrics.</DialogDescription>
        </DialogHeader>
        <div class="flex-1 w-full min-h-0 relative p-4">
             <div class="w-full h-full">
                <Line v-if="selectedChart === 'trend'" :data="chartData" :options="chartOptions" />
                <Doughnut v-if="selectedChart === 'distribution'" :data="radialData" :options="radialOptions" />
                <Radar v-if="selectedChart === 'health'" :data="radarData" :options="radarOptions" />
             </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>
