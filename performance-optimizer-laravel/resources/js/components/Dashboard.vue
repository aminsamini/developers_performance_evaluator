<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import {
  RefreshCw,
  TrendingUp,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  Activity,
  GitCommit,
  Clock,
  Archive,
  Filter,
  X,
  FileText
} from 'lucide-vue-next';
import { cn } from '@/lib/utils';
import { API_BASE_URL } from '../config';
import ActivityArchive from './ActivityArchive.vue';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
// Removed: Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle
// Removed: Menu

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

import { useGlobalState } from '@/composables/useGlobalState';

const router = useRouter();
const { developers, selectedTimezone, fetchDevelopers, refreshSignal } = useGlobalState();

// Remove local refs that are now global
// const developers = ref<Developer[]>([]); <-- Removed
// const selectedTimezone = ref('Asia/Tehran'); <-- Removed

const dateRange = ref({ start: null, end: null });
const summary = ref<any>(null);
const loading = ref(true); // general loading state
const metrics = ref<MetricResult[]>([]);
const lastSync = ref<string>('');
const error = ref('');

// Filter state for Activity Archive
const filterDeveloperId = ref<number | null>(null);
const filterDateFrom = ref('');
const filterDateTo = ref('');
const filterScoreMin = ref<number | ''>('');
const filterScoreMax = ref<number | ''>('');

const clearFilters = () => {
  filterDeveloperId.value = null;
  filterDateFrom.value = '';
  filterDateTo.value = '';
  filterScoreMin.value = '';
  filterScoreMax.value = '';
};

const hasActiveFilters = computed(() =>
  filterDeveloperId.value !== null ||
  filterDateFrom.value !== '' ||
  filterDateTo.value !== '' ||
  filterScoreMin.value !== '' ||
  filterScoreMax.value !== ''
);

// Fetch Data
const fetchExampleData = async () => {
    // Fallback or Initial Data
};

const fetchSummary = async (days: number = 7, developerId: number | null = null) => {
  try {
    let url = `${API_BASE_URL}/metrics/summary?days=${days}`;
    if (developerId) {
      url += `&developer_id=${developerId}`;
    }
    const response = await fetch(url);
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

// Local fetchDevelopers removed in favor of global state
// const fetchDevelopers = async () => { ... }

onMounted(() => {
  syncData();
  fetchDevelopers();
});

watch(refreshSignal, () => {
  console.log("Refresh signal received, syncing data...");
  syncData();
});

// Chart Logic
import { Input } from '@/components/ui/input'
import { Check, ChevronsUpDown, Search } from 'lucide-vue-next'

const selectedChart = ref<string | null>(null);

// Combobox Search State
const devSearchQuery = ref('');
const filteredComboboxDevelopers = computed(() => {
    if (!devSearchQuery.value) return developers.value;
    const q = devSearchQuery.value.toLowerCase();
    return developers.value.filter(d => d.name.toLowerCase().includes(q));
});

// Per-chart filter states
const chartFilters = ref<Record<string, { days: number; developerId: number | null; developerIds?: number[]; isComparison?: boolean; dateA?: string; dateB?: string; selectedFactors?: string[] }>>({
  trend: { days: 7, developerId: null, developerIds: [] },
  distribution: { days: 7, developerId: null },
  health: { days: 7, developerId: null, isComparison: false, dateA: new Date().toISOString().split('T')[0], dateB: new Date().toISOString().split('T')[0], selectedFactors: ['Score', 'Commits', 'Consistency', 'Team Size', 'Coverage'] }
});

// Per-chart data stores (separate from main summary)
const chartData_trend = ref<any>(null);
const chartData_distribution = ref<any>(null);
const chartData_health = ref<any>(null);
const chartData_health_compare = ref<any>(null); // For comparison mode

// Current chart filter accessors
const currentChartFilters = computed(() => {
  const chart = selectedChart.value || 'trend';
  return chartFilters.value[chart] || { days: 7, developerId: null };
});

// Fetch data for a specific chart
const fetchChartData = async (chartType: string) => {
  const filters = chartFilters.value[chartType];
  const fetchForParams = async (params: string) => {
      let url = `${API_BASE_URL}/metrics/summary?${params}`;
      // If specific ID is set AND multi-select is empty (or not exists), use backend filter.
      // If multi-select has values, we fetch ALL to filter on frontend.
      if (filters.developerId && (!filters.developerIds || filters.developerIds.length === 0)) {
          url += `&developer_id=${filters.developerId}`;
      }
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch chart data');
      return await res.json();
  };

  try {
    if (chartType === 'health' && filters.isComparison && filters.dateA && filters.dateB) {
        // Fetch Parallel
        const [dataA, dataB] = await Promise.all([
            fetchForParams(`date_from=${filters.dateA}&date_to=${filters.dateA}`),
            fetchForParams(`date_from=${filters.dateB}&date_to=${filters.dateB}`)
        ]);
        chartData_health.value = dataA;
        chartData_health_compare.value = dataB;
    } else {
        // Normal Fetch
        const data = await fetchForParams(`days=${filters.days}`);

        if (chartType === 'trend') chartData_trend.value = data;
        else if (chartType === 'distribution') chartData_distribution.value = data;
        else if (chartType === 'health') {
            chartData_health.value = data;
            chartData_health_compare.value = null; // Reset comparison
        }
    }
  } catch (err) {
    console.error(`Error fetching ${chartType} chart data:`, err);
  }
};

// When chart modal opens, fetch its data
watch(selectedChart, (newChart) => {
  if (newChart) {
    fetchChartData(newChart);
  }
});

// Update filter and refetch for current chart only
const updateChartFilter = (field: 'days' | 'developerId' | 'isComparison' | 'dateA' | 'dateB', value: any) => {
  const chart = selectedChart.value;
  if (chart) {
    chartFilters.value[chart][field] = value;
    fetchChartData(chart);
  }
};

const toggleChartFactor = (factor: string) => {
    const filters = chartFilters.value['health'];
    if (!filters) return;
    if (!filters.selectedFactors) filters.selectedFactors = ['Score', 'Commits', 'Consistency', 'Team Size', 'Coverage'];

    const idx = filters.selectedFactors.indexOf(factor);
    if (idx === -1) {
        filters.selectedFactors.push(factor);
    } else {
        // Prevent removing the last one (chart needs at least 1 dimension)
        if (filters.selectedFactors.length > 1) {
            filters.selectedFactors.splice(idx, 1);
        }
    }
};

// --- Summary Card Modal Logic ---
const selectedSummary = ref<string | null>(null);
const summaryDetails = ref<any[]>([]); // items for the list/table
const summaryFilters = ref({
  days: 30, // default to 30 days for details
  developerId: null as number | null
});

const summaryModalTitle = computed(() => {
    switch (selectedSummary.value) {
        case 'commits': return 'Total Commits Details';
        case 'developers': return 'Active Developers';
        case 'repos': return 'Tracked Repositories';
        case 'score': return 'Overall Score Breakdown';
        default: return 'Details';
    }
});

const summaryModalDescription = computed(() => {
    switch (selectedSummary.value) {
        case 'commits': return 'Detailed log of commits across all repositories.';
        case 'developers': return 'List of developers contributing in the selected period.';
        case 'repos': return 'All repositories currently being tracked and analyzed.';
        case 'score': return 'Performance scores breakdown by developer.';
        default: return 'View detailed metrics.';
    }
});

const fetchSummaryDetails = async () => {
    if (!selectedSummary.value) return;

    try {
        const type = selectedSummary.value;
        const days = summaryFilters.value.days;
        const devId = summaryFilters.value.developerId;

        // Calculate date range
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(endDate.getDate() - days);
        const fromStr = startDate.toISOString().split('T')[0];
        const toStr = endDate.toISOString().split('T')[0];

        if (type === 'repos') {
             // For repos, we just fetch the list. filtering by date/dev doesn't apply strictly to "tracked repos" existence,
             // but maybe we could show which have activity. For now simple list.
             const response = await fetch(`${API_BASE_URL}/repositories`);
             if (response.ok) {
                 summaryDetails.value = await response.json();
             }
        } else {
             // For others, we use the metrics endpoint to get raw data
             // We can use /metrics/ endpoint which lists all daily records
             let url = `${API_BASE_URL}/metrics/?skip=0&limit=1000`; // Fetch enough rows
             if (devId) url += `&developer_id=${devId}`;
             url += `&date_from=${fromStr}&date_to=${toStr}`;

             const response = await fetch(url);
             if (response.ok) {
                 const json = await response.json();
                 // API returns { data: [ { date: '...', items: [...] } ], ... }
                 // We need to flatten this into a single list of items with date attached
                 const flatList: any[] = [];
                 if (json.data && Array.isArray(json.data)) {
                    json.data.forEach((group: any) => {
                        if (group.items && Array.isArray(group.items)) {
                            group.items.forEach((item: any) => {
                                flatList.push({
                                    ...item,
                                    date: group.date,
                                    // Map backend keys to what template expects if needed
                                    commits_count: item.commits // Template expects item.commits_count? No wait template used commits_count in my previous view_file check?
                                    // Actually backend sends "commits", template was using "commits_count".
                                    // Let's standardise on what backend sends or map it.
                                    // Backend sends: commits, lines_added, lines_deleted, score, developer, developer_id
                                });
                            });
                        }
                    });
                 }
                 summaryDetails.value = flatList;
             }
        }
    } catch (err) {
        console.error("Error fetching summary details:", err);
        summaryDetails.value = [];
    }
};

watch([selectedSummary, summaryFilters], () => {
    if (selectedSummary.value) {
        fetchSummaryDetails();
    }
}, { deep: true });

const selectedChartTitle = computed(() => {
    switch (selectedChart.value) {
        case 'trend': return 'Performance Trend Analysis';
        case 'distribution': return 'Developer Contribution';
        case 'health': return 'Team Health Radar';
        default: return 'Chart Details';
    }
});

const selectedChartDescription = computed(() => {
    switch (selectedChart.value) {
        case 'trend':
            return 'Shows daily aggregated performance scores over time. Blue line represents this week, gray dashed line shows the previous week for comparison. Higher scores indicate better productivity.';
        case 'distribution':
            return 'Breakdown of total performance score by developer. Shows the contribution of top performers relative to the team total, highlighting workload distribution.';
        case 'health':
            return 'Radar chart showing team health across multiple dimensions: Score, Commits, Focus, Quality, Consistency, and Activity. Each axis represents how well the team performs in that area.';
        default:
            return 'Detailed breakdown of metrics.';
    }
});

// 1. Line Chart Data (Trend) - Now with previous week comparison
// Uses per-chart data when modal is open, otherwise uses main summary
// 1. Line Chart Data (Trend) - Now with previous week comparison OR Multi-Developer Comparison
// Uses per-chart data when modal is open, otherwise uses main summary
const chartData = computed(() => {
  const data = chartData_trend.value || summary.value;
  const labels = data?.trend?.labels || [];

  // Check for Multi-Select Filters
  const filters = currentChartFilters.value; // Access reactive filter
  const selectedIds = filters.developerIds || [];

  if (selectedIds.length > 0) {
      // MULTI-DEVELOPER MODE: Show one line per developer
      const datasets: any[] = [];
      const palette = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ec4899', '#ef4444', '#06b6d4', '#84cc16'];

      selectedIds.forEach((devId, idx) => {
          const dev = developers.value.find(d => d.id === devId);
          const devName = dev ? dev.name : `Dev ${devId}`;
          const color = palette[idx % palette.length];

          // Extract scores from daily_data
          const scores = (data.daily_data || []).map((day: any) => {
              // Find item for this developer
              const item = (day.items || []).find((i: any) => i.developer_id === devId);
              return item ? (item.score || 0) : 0;
          });

          // Ensure score array matches labels length (padding if needed, though daily_data usually matches days param)
          // Ideally rely on API correctness or map by date label if labels are dates.
          // Assuming API returns daily_data in same order as labels.

          datasets.push({
              label: devName,
              data: scores,
              borderColor: color,
              backgroundColor: color, // For legend
              tension: 0.4,
              fill: false,
              pointRadius: 4,
              pointHoverRadius: 6,
              borderWidth: 2
          });
      });

      return { labels, datasets };
  }

  // DEFAULT MODE: Total Score + Previous Week Comparison
  return {
    labels: labels,
    datasets: [
      {
        label: 'Previous Week',
        data: data?.trend?.prev_scores || [],
        borderColor: '#9ca3af', // gray-400
        backgroundColor: 'rgba(156, 163, 175, 0.2)', // gray-400 with low opacity
        tension: 0.4,
        fill: true,
        pointRadius: 0,
        pointHoverRadius: 4,
        borderWidth: 1,
        borderDash: [5, 5],
        order: 1  // Draw behind current week
      },
      {
        label: 'This Week',
        data: data?.trend?.scores || [],
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
        borderWidth: 2,
        order: 0  // Draw on top
      }
    ],
  };
});

// 2. Radial Data (Developer Contribution)
// Shows share of Total Score by Top Developers
const radialData = computed(() => {
  // Use per-chart data if available, otherwise fall back to summary
  const data = chartData_distribution.value || summary.value;

  if (!data?.leaderboard || data.leaderboard.length === 0) {
    return { labels: ['No Data'], datasets: [{ data: [1], backgroundColor: ['#e2e8f0'] }] };
  }

  // Logic: Show Top 5 Developers + "Others"
  // If filtered by developer, show "Selected Developer" vs "Rest of Team"

  const leaderboard = [...data.leaderboard].sort((a, b) => b.total_score - a.total_score);
  const totalScore = data.totals?.total_score || leaderboard.reduce((sum, d) => sum + (d.total_score || 0), 0);

  // If no score at all
  if (totalScore === 0) {
      return { labels: ['No Activity'], datasets: [{ data: [1], backgroundColor: ['#f3f4f6'] }] };
  }

  let labels: string[] = [];
  let values: number[] = [];
  let colors: string[] = [];

  const palette = [
    '#3b82f6', // blue-500
    '#10b981', // green-500
    '#8b5cf6', // purple-500
    '#f59e0b', // amber-500
    '#ec4899', // pink-500
    '#6b7280'  // gray-500 (Others)
  ];

  const currentFilterDevId = currentChartFilters.value.developerId;

  if (currentFilterDevId) {
      // Filtered View: Selected Dev vs Others
      const selectedDev = leaderboard.find(d => d.developer_id === currentFilterDevId || d.id === currentFilterDevId); // Handle inconsistency if any
      const selectedName = selectedDev ? selectedDev.name : 'Selected Developer';
      const selectedScore = selectedDev ? (selectedDev.total_score || 0) : 0;
      const otherScore = totalScore - selectedScore;

      labels = [selectedName, 'Rest of Team'];
      values = [selectedScore, otherScore];
      colors = ['#3b82f6', '#e5e7eb']; // Highlight vs Gray
  } else {
      // Team View: Top 5 + Others
      const top5 = leaderboard.slice(0, 5);
      const others = leaderboard.slice(5);

      labels = top5.map(d => d.name);
      values = top5.map(d => d.total_score || 0);
      colors = palette.slice(0, top5.length);

      const othersScore = others.reduce((sum, d) => sum + (d.total_score || 0), 0);
      if (othersScore > 0) {
          labels.push(`Others (${others.length})`);
          values.push(othersScore);
          colors.push(palette[5]);
      }
  }

  return {
    labels: labels,
    datasets: [{
      data: values,
      backgroundColor: colors,
      borderColor: '#ffffff',
      borderWidth: 2,
      hoverOffset: 4
    }]
  };
});

// 3. Radar Data (Team Health) - Uses actual calculated metrics
const radarData = computed(() => {
  const calculateHealthMetrics = (data: any) => {
      if (!data?.leaderboard || data.leaderboard.length === 0) return [0, 0, 0, 0, 0];

      const leaderboard = data.leaderboard;
      const totals = data.totals || {};

      const avgScore = leaderboard.reduce((sum: number, d: any) => sum + (d.avg_score || 0), 0) / leaderboard.length;
      const totalCommits = totals.total_commits || 0;
      const activeDevelopers = totals.active_developers || leaderboard.length;
      const daysTracked = totals.days_tracked || 1; // avoid div by 0

      // Normalized metrics (0-100)
      const scoreHealth = Math.min(avgScore, 100);
      const commitHealth = Math.min((totalCommits / (activeDevelopers * 7 * 5)) * 100, 100);
      const consistencyHealth = Math.min((daysTracked / 7) * 100, 100);
      const teamHealth = Math.min((activeDevelopers / 5) * 100, 100);
      const coverageHealth = Math.min((leaderboard.filter((d: any) => d.days_active > 0).length / leaderboard.length) * 100, 100);

      return [scoreHealth, commitHealth, consistencyHealth, teamHealth, coverageHealth];
  };

  // Fix: Define filters here
  const filters = chartFilters.value.health;

  // Filter Labels & Data based on selectedFactors
  const allLabels = ['Score', 'Commits', 'Consistency', 'Team Size', 'Coverage'];
  const selectedLabels = (filters.selectedFactors && filters.selectedFactors.length > 0)
      ? filters.selectedFactors
      : allLabels;

  const filterMetrics = (fullMetrics: number[]) => {
       // Map full metric array to labels
       const metricMap = new Map();
       allLabels.forEach((label, idx) => metricMap.set(label, fullMetrics[idx]));
       // Return only selected metrics
       return selectedLabels.map(label => metricMap.get(label) || 0);
  };

  // COMPARISON MODE
  if (filters.isComparison) {
      const metricsA = calculateHealthMetrics(chartData_health.value);
      const metricsB = calculateHealthMetrics(chartData_health_compare.value);

      return {
          labels: selectedLabels,
          datasets: [
              {
                  label: `Date: ${filters.dateA}`,
                  data: filterMetrics(metricsA),
                  backgroundColor: 'rgba(59, 130, 246, 0.2)', // blue
                  borderColor: '#3b82f6',
                  pointBackgroundColor: '#3b82f6',
                  fill: true
              },
              {
                  label: `Date: ${filters.dateB}`,
                  data: filterMetrics(metricsB),
                  backgroundColor: 'rgba(236, 72, 153, 0.2)', // pink
                  borderColor: '#ec4899',
                  pointBackgroundColor: '#ec4899',
                  fill: true
              }
          ]
      };
  }

  // STANDARD MODE
  const data = chartData_health.value || summary.value;
  const metrics = calculateHealthMetrics(data);

  return {
    labels: selectedLabels,
    datasets: [{
      label: 'Team Health',
      data: filterMetrics(metrics),
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

// 4. Card Summary Metrics (Dynamic)
const cardMetrics = computed(() => {
    if (!summary.value) return { trend: 0, contribution: 0, health: 0 };

    // 1. Trend %
    const currentScore = summary.value.trend.scores.reduce((a: number, b: number) => a + b, 0);
    const prevScore = summary.value.trend.prev_scores.reduce((a: number, b: number) => a + b, 0);
    const trend = prevScore > 0 ? ((currentScore - prevScore) / prevScore) * 100 : 0;

    // 2. Contribution (Share of Top 3)
    // Used to be Diversity Score, now "Top 3 Impact"
    const sorted = [...(summary.value.leaderboard || [])].sort((a, b) => (b.total_score || 0) - (a.total_score || 0));
    const total = sorted.reduce((sum, d) => sum + (d.total_score || 0), 0);
    const top3 = sorted.slice(0, 3).reduce((sum, d) => sum + (d.total_score || 0), 0);
    const contribution = total > 0 ? (top3 / total) * 100 : 0;

    // 3. Overall Health (Avg of radar metrics)
    // Re-calculating simplified version of radar stats
    const totals = summary.value.totals || {};
    const activeDevs = totals.active_developers || 0;
    const avgScore = sorted.length > 0 ? (sorted.reduce((sum, d) => sum + (d.avg_score || 0), 0) / sorted.length) : 0;

    // Factors (0-100)
    const f_score = Math.min(avgScore, 100);
    const f_consistency = Math.min(((totals.days_tracked || 0) / 7) * 100, 100);
    const f_activity = Math.min((activeDevs / 5) * 100, 100); // Target 5 devs

    const health = (f_score + f_consistency + f_activity) / 3;

    return {
        trend,
        contribution,
        health
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
        legend: {
            display: true,
            position: 'right' as const,
            labels: {
                usePointStyle: true,
                boxWidth: 8
            }
        },
        tooltip: {
            enabled: true,
            // filter: (item: any) => item.dataIndex === 0 // Show tooltip only for the value segment
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
  <div class="flex-1 space-y-4 p-8 pt-6">
    <!-- Removed Header Section (Moved to NavBar) -->

    <!-- Summary Stats Row -->
    <div v-if="summary" class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card class="cursor-pointer transition-all hover:shadow-lg hover:border-primary/50" @click="selectedSummary = 'commits'">
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Total Commits</CardTitle>
          <GitCommit class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{{ summary.totals.commits ?? summary.totals.total_commits ?? 0 }}</div>
          <p class="text-xs text-muted-foreground">Across all repos</p>
        </CardContent>
      </Card>
      <Card class="cursor-pointer transition-all hover:shadow-lg hover:border-primary/50" @click="selectedSummary = 'developers'">
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Active Developers</CardTitle>
          <Activity class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{{ summary.totals.active_developers ?? summary.totals.developers ?? 0 }}</div>
          <p class="text-xs text-muted-foreground">Contributing this week</p>
        </CardContent>
      </Card>
       <Card class="cursor-pointer transition-all hover:shadow-lg hover:border-primary/50" @click="selectedSummary = 'repos'">
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Tracked Repos</CardTitle>
          <Archive class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{{ summary.totals.repo_count ?? summary.totals.repos ?? 0 }}</div>
          <p class="text-xs text-muted-foreground">Active repositories</p>
        </CardContent>
      </Card>
      <Card class="cursor-pointer transition-all hover:shadow-lg hover:border-primary/50" @click="selectedSummary = 'score'">
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
                    <div class="flex items-center gap-2 leading-none font-medium" :class="cardMetrics.trend >= 0 ? 'text-green-600' : 'text-red-500'">
                      Trending {{ cardMetrics.trend >= 0 ? 'up' : 'down' }} by {{ Math.abs(cardMetrics.trend).toFixed(1) }}% <TrendingUp class="h-4 w-4" :class="{'rotate-180': cardMetrics.trend < 0}" />
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
                    <div class="flex items-center gap-2 leading-none font-medium text-blue-600">
                    Top 3 Impact: {{ cardMetrics.contribution.toFixed(0) }}% <Activity class="h-4 w-4" />
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
                    Overall Health: {{ cardMetrics.health.toFixed(0) }}% <TrendingUp class="h-4 w-4" />
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



        <!-- Best Score Day Card -->
        <Card v-if="summary?.best_day" class="border-primary/20 bg-gradient-to-br from-primary/5 to-background">
            <CardHeader class="pb-2">
                <CardTitle class="flex items-center gap-2 text-primary">
                    <Trophy class="h-5 w-5 text-amber-500" />
                    Best Performance Day
                </CardTitle>
                <CardDescription>Highest scoring day in period</CardDescription>
            </CardHeader>
            <CardContent>
                <div class="flex flex-col gap-4">
                    <div class="flex items-baseline justify-between border-b pb-2">
                         <div>
                            <div class="text-2xl font-bold tracking-tight">{{ summary.best_day.date }}</div>
                            <div class="text-sm text-muted-foreground font-medium">{{ summary.best_day.weekday }}</div>
                         </div>
                         <div class="text-right">
                             <div class="text-xl font-bold text-primary">{{ summary.best_day.score?.toLocaleString() }} pts</div>
                             <div class="text-xs text-muted-foreground">{{ summary.best_day.commits }} commits</div>
                         </div>
                    </div>
                    <div class="flex items-center justify-between text-sm">
                        <span class="text-muted-foreground">Top Contributor:</span>
                        <span class="font-medium flex items-center gap-1">
                            <User class="h-3 w-3" /> {{ summary.best_day.top_contributor }}
                        </span>
                    </div>
                    <!-- Small Active Devs Stat -->
                    <div class="flex items-center justify-between text-xs text-muted-foreground">
                        <span>Active Developers:</span>
                        <span>{{ summary.best_day.active_devs }} devs</span>
                    </div>
                </div>
            </CardContent>
        </Card>

        <!-- Filter Section -->
        <Card>
          <CardHeader class="pb-3">
            <CardTitle class="flex items-center gap-2 text-base">
              <Filter class="h-4 w-4" />
              Archive Filters
            </CardTitle>
            <CardDescription>Filter Activity Archive results</CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="space-y-2">
              <label class="text-sm font-medium">Developer</label>
              <select
                v-model="filterDeveloperId"
                class="w-full h-9 px-3 rounded-md border border-input bg-background text-sm"
              >
                <option :value="null">All Developers</option>
                <option v-for="dev in developers" :key="dev.id" :value="dev.id">
                  {{ dev.name }}
                </option>
              </select>
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Date Range</label>
              <div class="grid grid-cols-2 gap-2">
                <input
                  type="date"
                  v-model="filterDateFrom"
                  placeholder="From"
                  class="h-9 px-3 rounded-md border border-input bg-background text-sm"
                />
                <input
                  type="date"
                  v-model="filterDateTo"
                  placeholder="To"
                  class="h-9 px-3 rounded-md border border-input bg-background text-sm"
                />
              </div>
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Score Range</label>
              <div class="grid grid-cols-2 gap-2">
                <input
                  type="number"
                  v-model="filterScoreMin"
                  placeholder="Min (0)"
                  min="0"
                  max="100"
                  class="h-9 px-3 rounded-md border border-input bg-background text-sm"
                />
                <input
                  type="number"
                  v-model="filterScoreMax"
                  placeholder="Max (100)"
                  min="0"
                  max="100"
                  class="h-9 px-3 rounded-md border border-input bg-background text-sm"
                />
              </div>
            </div>
            <Button
              v-if="hasActiveFilters"
              variant="outline"
              size="sm"
              class="w-full"
              @click="clearFilters"
            >
              <X class="h-4 w-4 mr-2" />
              Clear Filters
            </Button>
          </CardContent>
        </Card>

        <RepositoryManager @dataUpdated="syncData" />
      </div>

      <!-- Activity Column -->
      <div class="md:col-span-2 flex flex-col gap-6">
        <ActivityArchive
          :timezone="selectedTimezone"
          :developer-id="filterDeveloperId"
          :date-from="filterDateFrom"
          :date-to="filterDateTo"
          :score-min="filterScoreMin"
          :score-max="filterScoreMax"
        />
      </div>
    </div>

    <!-- Chart Modal (Teleported via Dialog) -->
    <!-- We place it here; Shadcn Dialog renders to body usually -->
    <Dialog :open="!!selectedChart" @update:open="(val) => !val && (selectedChart = null)">
      <DialogContent class="max-w-5xl w-full h-[85vh] flex flex-col z-[100]" style="z-index: 100;">
        <DialogHeader>
          <DialogTitle>{{ selectedChartTitle }}</DialogTitle>
          <DialogDescription class="text-sm text-muted-foreground mt-1">
            {{ selectedChartDescription }}
          </DialogDescription>
        </DialogHeader>

        <!-- Chart Filters -->
        <div class="flex flex-wrap items-center gap-4 px-4 py-3 bg-muted/30 rounded-lg border">

          <!-- Comparison Mode Toggle (Health Chart Only) -->
          <div v-if="selectedChart === 'health'" class="flex items-center gap-2 mr-4 border-r pr-4">
              <label class="text-sm font-medium whitespace-nowrap flex items-center gap-2 cursor-pointer">
                  <input type="checkbox"
                         :checked="currentChartFilters.isComparison"
                         @change="updateChartFilter('isComparison', ($event.target as HTMLInputElement).checked)"
                         class="rounded border-gray-300 text-primary shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50" />
                  Comparison Mode
              </label>
          </div>

          <!-- Time Period (Standard) -->
          <div v-if="!currentChartFilters.isComparison" class="flex items-center gap-2">
            <label class="text-sm font-medium whitespace-nowrap">Time Period:</label>
            <select
              :value="currentChartFilters.days"
              @change="updateChartFilter('days', Number(($event.target as HTMLSelectElement).value))"
              class="h-8 px-2 rounded-md border border-input bg-background text-sm"
            >
              <option :value="7">Last 7 Days</option>
              <option :value="14">Last 14 Days</option>
              <option :value="30">Last 30 Days</option>
              <option :value="60">Last 60 Days</option>
              <option :value="90">Last 90 Days</option>
            </select>
          </div>

          <!-- Date Comparison Pickers -->
          <div v-else class="flex items-center gap-4">
              <div class="flex items-center gap-2">
                  <label class="text-sm font-medium text-blue-600">Date A:</label>
                  <input type="date"
                         :value="currentChartFilters.dateA"
                         @change="updateChartFilter('dateA', ($event.target as HTMLInputElement).value)"
                         class="h-8 px-2 rounded-md border border-input bg-background text-sm" />
              </div>
              <div class="flex items-center gap-2">
                  <label class="text-sm font-medium text-pink-600">Date B:</label>
                  <input type="date"
                         :value="currentChartFilters.dateB"
                         @change="updateChartFilter('dateB', ($event.target as HTMLInputElement).value)"
                         class="h-8 px-2 rounded-md border border-input bg-background text-sm" />
              </div>
          </div>

          <!-- Customizable Criteria (Health Only) -->
          <div v-if="selectedChart === 'health'" class="flex flex-col sm:flex-row items-start sm:items-center gap-2 border-l pl-4 ml-2">
            <span class="text-sm font-medium text-muted-foreground mr-1">Criteria:</span>
            <div class="flex flex-wrap gap-2">
                <label v-for="factor in ['Score', 'Commits', 'Consistency', 'Team Size', 'Coverage']"
                       :key="factor"
                       class="text-xs flex items-center gap-1.5 cursor-pointer px-2 py-1 rounded border transition-colors"
                       :class="(currentChartFilters.selectedFactors || []).includes(factor) ? 'bg-primary/10 border-primary/20 text-primary' : 'bg-background hover:bg-muted text-muted-foreground'"
                >
                    <input type="checkbox"
                        :checked="(currentChartFilters.selectedFactors || []).includes(factor)"
                        @change="toggleChartFactor(factor)"
                        class="rounded border-gray-300 text-primary h-3 w-3 focus:ring-0" />
                    {{ factor }}
                </label>
            </div>
          </div>

          <div class="flex items-center gap-2 ml-auto">
            <label class="text-sm font-medium whitespace-nowrap">Developer:</label>

            <!-- Multi-Select Combobox for Trend -->
            <Popover v-if="selectedChart === 'trend'">
                <PopoverTrigger as-child>
                    <Button variant="outline" role="combobox" class="h-8 w-[200px] justify-between text-sm px-2">
                        <span class="truncate">
                            <span v-if="(!currentChartFilters.developerIds || currentChartFilters.developerIds.length === 0)">
                                All Developers
                            </span>
                            <span v-else>
                                {{ currentChartFilters.developerIds.length }} Selected
                            </span>
                        </span>
                        <ChevronsUpDown class="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                </PopoverTrigger>
                <PopoverContent class="w-[200px] p-0 z-[200]" align="end">
                    <div class="p-2 pb-0">
                        <div class="flex items-center border rounded-md px-2 bg-background mb-2">
                            <Search class="h-4 w-4 text-muted-foreground mr-1" />
                            <input
                                v-model="devSearchQuery"
                                class="flex h-8 w-full rounded-md bg-transparent py-2 text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
                                placeholder="Search..."
                            />
                        </div>
                    </div>
                    <div class="max-h-[300px] overflow-y-auto p-1 space-y-0.5">
                        <!-- All Developers Option -->
                        <div class="flex items-center px-2 py-1.5 rounded-sm cursor-pointer hover:bg-accent hover:text-accent-foreground text-sm"
                             @click="updateChartFilter('developerIds', [])">
                             <Check class="mr-2 h-4 w-4"
                                    :class="(!currentChartFilters.developerIds || currentChartFilters.developerIds.length === 0) ? 'opacity-100' : 'opacity-0'" />
                             <span>All Developers</span>
                        </div>

                        <!-- Filtered List -->
                        <div v-for="dev in filteredComboboxDevelopers" :key="dev.id"
                               class="flex items-center px-2 py-1.5 rounded-sm cursor-pointer hover:bg-accent hover:text-accent-foreground text-sm"
                               @click="() => {
                                    const ids = [...(currentChartFilters.developerIds || [])];
                                    const idx = ids.indexOf(dev.id);
                                    if (idx > -1) ids.splice(idx, 1);
                                    else ids.push(dev.id);
                                    updateChartFilter('developerIds', ids);
                               }">
                             <Check class="mr-2 h-4 w-4"
                                    :class="(currentChartFilters.developerIds || []).includes(dev.id) ? 'opacity-100' : 'opacity-0'" />
                             <span>{{ dev.name }}</span>
                        </div>
                        <div v-if="filteredComboboxDevelopers.length === 0" class="py-6 text-center text-sm text-muted-foreground">
                            No developer found.
                        </div>
                    </div>
                </PopoverContent>
            </Popover>

            <!-- Legacy Select for Other Charts -->
            <select v-else
              :value="currentChartFilters.developerId"
              @change="updateChartFilter('developerId', ($event.target as HTMLSelectElement).value === '' ? null : Number(($event.target as HTMLSelectElement).value))"
              class="h-8 px-2 rounded-md border border-input bg-background text-sm min-w-[150px]"
            >
              <option value="">All Developers</option>
              <option v-for="dev in developers" :key="dev.id" :value="dev.id">
                {{ dev.name }}
              </option>
            </select>
          </div>
          <div class="text-xs text-muted-foreground ml-auto">
            <span v-if="currentChartFilters.developerId">Filtered view</span>
            <span v-else>Team aggregate</span>
          </div>
        </div>

        <!-- Chart Area -->
        <div class="flex-1 w-full min-h-0 relative p-4">
             <div class="w-full h-full">
                <Line v-if="selectedChart === 'trend'" :data="chartData" :options="chartOptions" />
                <Doughnut v-if="selectedChart === 'distribution'" :data="radialData" :options="radialOptions" />
                <Radar v-if="selectedChart === 'health'" :data="radarData" :options="radarOptions" />
             </div>
        </div>
      </DialogContent>
    </Dialog>

    <!-- Summary Details Modal -->
    <Dialog :open="!!selectedSummary" @update:open="(val) => !val && (selectedSummary = null)">
      <DialogContent class="max-w-4xl w-full max-h-[85vh] flex flex-col z-[100]" style="z-index: 100;">
        <DialogHeader>
          <DialogTitle>{{ summaryModalTitle }}</DialogTitle>
          <DialogDescription class="text-sm text-muted-foreground">
            {{ summaryModalDescription }}
          </DialogDescription>
        </DialogHeader>

        <!-- Filters (Hidden for Repos) -->
        <div v-if="selectedSummary !== 'repos'" class="flex flex-wrap items-center gap-4 px-4 py-3 bg-muted/30 rounded-lg border">
            <div class="flex items-center gap-2">
                <label class="text-sm font-medium whitespace-nowrap">Duration:</label>
                <select v-model="summaryFilters.days" class="h-8 px-2 rounded-md border border-input bg-background text-sm">
                    <option :value="7">Last 7 Days</option>
                    <option :value="14">Last 14 Days</option>
                    <option :value="30">Last 30 Days</option>
                    <option :value="60">Last 60 Days</option>
                    <option :value="90">Last 90 Days</option>
                </select>
            </div>
            <div class="flex items-center gap-2">
                <label class="text-sm font-medium whitespace-nowrap">Developer:</label>
                <select v-model="summaryFilters.developerId" class="h-8 px-2 rounded-md border border-input bg-background text-sm min-w-[150px]">
                    <option :value="null">All Developers</option>
                    <option v-for="dev in developers" :key="dev.id" :value="dev.id">{{ dev.name }}</option>
                </select>
            </div>
        </div>

        <!-- Content Area -->
        <div class="flex-1 w-full min-h-0 relative p-4 overflow-y-auto">

            <!-- Table: Repos -->
            <div v-if="selectedSummary === 'repos'">
                <table class="w-full text-sm text-left">
                    <thead class="text-xs text-muted-foreground uppercase bg-muted/50 sticky top-0">
                        <tr>
                            <th class="px-4 py-3">Repository</th>
                            <th class="px-4 py-3">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="repo in summaryDetails" :key="repo.id || repo.name" class="border-b">
                            <td class="px-4 py-3 font-medium">{{ repo.name }}</td>
                            <td class="px-4 py-3 text-green-600">Active</td>
                        </tr>
                         <tr v-if="summaryDetails.length === 0">
                            <td colspan="2" class="px-4 py-6 text-center text-muted-foreground">No repositories found.</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Table: Commits/Score/Devs (Based on raw metrics) -->
            <div v-else>
                 <table class="w-full text-sm text-left">
                    <thead class="text-xs text-muted-foreground uppercase bg-muted/50 sticky top-0">
                        <tr>
                            <th class="px-4 py-3">Date</th>
                            <!-- Only show Developer column if not filtering by one -->
                            <th v-if="!summaryFilters.developerId" class="px-4 py-3">Developer</th>
                            <th class="px-4 py-3 text-right">Commits</th>
                            <th class="px-4 py-3 text-right">Score</th>
                            <th v-if="selectedSummary === 'commits'" class="px-4 py-3 text-right">Lines +/-</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="item in summaryDetails" :key="item.id" class="border-b hover:bg-muted/50 transition-colors">
                            <td class="px-4 py-3 whitespace-nowrap">{{ item.date }}</td>
                            <td v-if="!summaryFilters.developerId" class="px-4 py-3 font-medium">
                                {{ item.developer || 'Unknown' }}
                            </td>
                            <td class="px-4 py-3 text-right font-mono">{{ item.commits }}</td>
                            <td class="px-4 py-3 text-right font-mono font-medium">{{ item.score?.toFixed(1) }}</td>
                            <td v-if="selectedSummary === 'commits'" class="px-4 py-3 text-right text-xs text-muted-foreground">
                                <span class="text-green-600">+{{ item.lines_added }}</span> / <span class="text-red-600">-{{ item.lines_deleted }}</span>
                            </td>
                        </tr>
                        <tr v-if="summaryDetails.length === 0">
                            <td colspan="5" class="px-4 py-8 text-center text-muted-foreground">
                                No records found for this period.
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>
