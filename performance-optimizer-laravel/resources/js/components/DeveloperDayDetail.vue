<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { API_BASE_URL } from '../config';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress'
import { Doughnut } from 'vue-chartjs';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

interface Props {
  visible: boolean;
  developerId: number | null;
  developerName: string;
  date: string;
}

interface ScoreBreakdown {
  total: number;
  has_activity: boolean;
  time_score?: number;
  components?: Record<string, { value: number; points: number; weight: number }>;
}

interface DetailData {
  developer: string;
  date: string;
  score: number;
  score_breakdown: ScoreBreakdown;
  metrics: {
    commits: number;
    lines_added: number;
    lines_deleted: number;
    files_modified: number;
    churn_score: number;
    coding_time_seconds: number;
    active_coding_seconds: number;
    deep_work_seconds: number;
    start_time: string | null;
    end_time: string | null;
    focus_ratio: number;
    context_switches: number;
  };
  wakatime_details: {
    languages?: { name: string; percent: number; text: string }[];
    projects?: { name: string; percent: number; text: string }[];
  } | null;
}

const props = defineProps<Props>();
const emit = defineEmits(['update:visible']);

const loading = ref(false);
const error = ref('');
const detail = ref<DetailData | null>(null);

const dialogOpen = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
});

// Language chart data
const languageChartData = computed(() => {
  const languages = detail.value?.wakatime_details?.languages || [];
  const top5 = languages.slice(0, 5);
  return {
    labels: top5.map(l => l.name),
    datasets: [{
      data: top5.map(l => l.percent),
      backgroundColor: [
        'rgba(99, 102, 241, 0.8)',
        'rgba(34, 197, 94, 0.8)',
        'rgba(234, 179, 8, 0.8)',
        'rgba(239, 68, 68, 0.8)',
        'rgba(168, 85, 247, 0.8)'
      ]
    }]
  };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'right' as const,
      labels: {
        boxWidth: 12
      }
    }
  }
};

const formatMinutes = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const hrs = Math.floor(mins / 60);
  const remainMins = mins % 60;
  if (hrs > 0) return `${hrs}h ${remainMins}m`;
  return `${mins}m`;
};

const fetchDetail = async () => {
  if (!props.developerId || !props.date) return;

  loading.value = true;
  error.value = '';
  detail.value = null;

  try {
    const response = await fetch(`${API_BASE_URL}/metrics/detail/${props.developerId}/${props.date}`);
    if (!response.ok) {
      throw new Error(await response.text());
    }
    detail.value = await response.json();
  } catch (err) {
    error.value = `Failed to load details: ${err}`;
  } finally {
    loading.value = false;
  }
};

watch(() => props.visible, (newVal) => {
  if (newVal && props.developerId && props.date) {
    fetchDetail();
  }
});
</script>

<template>
  <Dialog v-model:open="dialogOpen">
    <DialogContent class="sm:max-w-[900px] h-[90vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>{{ developerName }} - {{ date }}</DialogTitle>
      </DialogHeader>

      <div v-if="loading" class="text-center p-8">
         <p>Loading details...</p>
      </div>

    <div v-else-if="error">
        <Alert variant="destructive">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{{ error }}</AlertDescription>
        </Alert>
    </div>

    <div v-else-if="detail" class="space-y-6">
      <!-- Score Overview -->
      <div class="text-center p-4 bg-muted rounded-lg">
        <div class="text-5xl font-bold" :class="detail.score > 50 ? 'text-green-600' : detail.score > 0 ? 'text-yellow-600' : 'text-gray-400'">
          {{ detail.score.toFixed(1) }}
        </div>
        <div class="text-sm text-muted-foreground mt-1">Total Score</div>
        <Badge v-if="!detail.score_breakdown.has_activity" variant="secondary" class="mt-2">No Activity</Badge>
      </div>

      <!-- Score Breakdown -->
      <div v-if="detail.score_breakdown.has_activity && detail.score_breakdown.components" class="space-y-3">
        <h4 class="font-semibold text-foreground">Score Breakdown</h4>

        <div class="grid grid-cols-2 gap-3">
          <div v-for="(comp, key) in detail.score_breakdown.components" :key="key"
               class="p-3 bg-muted/50 rounded-lg">
            <div class="flex justify-between items-center mb-1">
              <span class="text-sm text-foreground capitalize">{{ key.replace(/_/g, ' ') }}</span>
              <span class="font-bold" :class="comp.points >= 0 ? 'text-green-600' : 'text-red-500'">
                {{ comp.points > 0 ? '+' : '' }}{{ comp.points.toFixed(1) }}
              </span>
            </div>
            <div class="text-xs text-muted-foreground">
              {{ comp.value }} × {{ comp.weight }}
            </div>
          </div>
        </div>
      </div>

      <!-- Metrics Grid -->
      <div class="grid grid-cols-3 gap-4">
        <div class="text-center p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
          <div class="text-2xl font-bold text-blue-600">{{ detail.metrics.commits }}</div>
          <div class="text-xs text-muted-foreground">Commits</div>
        </div>
        <div class="text-center p-3 bg-green-50 dark:bg-green-950/20 rounded-lg">
          <div class="text-2xl font-bold text-green-600">{{ detail.metrics.files_modified }}</div>
          <div class="text-xs text-muted-foreground">Files Modified</div>
        </div>
        <div class="text-center p-3 bg-purple-50 dark:bg-purple-950/20 rounded-lg">
          <div class="text-2xl font-bold text-purple-600">
            {{ formatMinutes(detail.metrics.active_coding_seconds) }}
          </div>
          <div class="text-xs text-muted-foreground">Active Coding</div>
        </div>
      </div>

      <!-- Time Details -->
      <div class="grid grid-cols-2 gap-4">
        <div class="p-3 bg-muted/50 rounded-lg">
          <div class="text-sm text-muted-foreground">Work Hours</div>
          <div class="font-medium text-foreground">
            {{ detail.metrics.start_time || '—' }} - {{ detail.metrics.end_time || '—' }}
          </div>
        </div>
        <div class="p-3 bg-muted/50 rounded-lg">
          <div class="text-sm text-muted-foreground">Deep Work</div>
          <div class="font-medium text-foreground">{{ formatMinutes(detail.metrics.deep_work_seconds) }}</div>
        </div>
      </div>

      <!-- Focus & Churn -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <div class="flex justify-between text-sm mb-1">
            <span class="text-muted-foreground">Focus Ratio</span>
            <span class="font-medium text-foreground">{{ (detail.metrics.focus_ratio * 100).toFixed(0) }}%</span>
          </div>
          <Progress :model-value="detail.metrics.focus_ratio * 100" />
        </div>
        <div>
          <div class="flex justify-between text-sm mb-1">
            <span class="text-muted-foreground">Code Stability</span>
            <span class="font-medium text-foreground">{{ ((1 - detail.metrics.churn_score) * 100).toFixed(0) }}%</span>
          </div>
          <Progress :model-value="(1 - detail.metrics.churn_score) * 100" />
        </div>
      </div>

      <!-- Lines Changed -->
      <div class="p-3 bg-muted/50 rounded-lg">
        <div class="text-sm text-muted-foreground mb-2">Lines Changed</div>
        <div class="flex gap-4">
          <span class="text-green-600">+{{ detail.metrics.lines_added }} added</span>
          <span class="text-red-500">-{{ detail.metrics.lines_deleted }} deleted</span>
        </div>
      </div>

      <!-- Languages Chart -->
      <div v-if="detail.wakatime_details?.languages?.length" class="p-4 bg-muted/50 rounded-lg">
        <h4 class="font-semibold text-foreground mb-3">Languages</h4>
        <div style="height: 150px;">
          <Doughnut :data="languageChartData" :options="chartOptions" />
        </div>
      </div>

      <!-- Projects -->
      <div v-if="detail.wakatime_details?.projects?.length" class="p-4 bg-muted/50 rounded-lg">
        <h4 class="font-semibold text-foreground mb-3">Projects</h4>
        <div class="flex flex-wrap gap-2">
          <Badge v-for="proj in detail.wakatime_details.projects" :key="proj.name" variant="secondary">
            {{ proj.name }}: {{ proj.text }}
          </Badge>
        </div>
      </div>
    </div>
    </DialogContent>
  </Dialog>
</template>
