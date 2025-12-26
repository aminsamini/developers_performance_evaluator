<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { API_BASE_URL } from '../config';
import Dialog from 'primevue/dialog';
import Tag from 'primevue/tag';
import Message from 'primevue/message';
import ProgressBar from 'primevue/progressbar';
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

const dialogVisible = computed({
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
  <Dialog v-model:visible="dialogVisible" :header="`${developerName} - ${date}`" :modal="true" class="w-full md:w-50rem">
    <div v-if="loading" class="text-center p-8">
      <i class="pi pi-spin pi-spinner text-4xl text-indigo-600"></i>
      <p class="mt-2 text-gray-500">Loading details...</p>
    </div>
    
    <Message v-else-if="error" severity="error" :closable="false">{{ error }}</Message>
    
    <div v-else-if="detail" class="space-y-6">
      <!-- Score Overview -->
      <div class="text-center p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg">
        <div class="text-5xl font-bold" :class="detail.score > 50 ? 'text-green-600' : detail.score > 0 ? 'text-yellow-600' : 'text-gray-400'">
          {{ detail.score.toFixed(1) }}
        </div>
        <div class="text-sm text-gray-500 mt-1">Total Score</div>
        <Tag v-if="!detail.score_breakdown.has_activity" severity="secondary" value="No Activity" class="mt-2" />
      </div>

      <!-- Score Breakdown -->
      <div v-if="detail.score_breakdown.has_activity && detail.score_breakdown.components" class="space-y-3">
        <h4 class="font-semibold text-gray-700">Score Breakdown</h4>
        
        <div class="grid grid-cols-2 gap-3">
          <div v-for="(comp, key) in detail.score_breakdown.components" :key="key" 
               class="p-3 bg-gray-50 rounded-lg">
            <div class="flex justify-between items-center mb-1">
              <span class="text-sm text-gray-600 capitalize">{{ key.replace(/_/g, ' ') }}</span>
              <span class="font-bold" :class="comp.points >= 0 ? 'text-green-600' : 'text-red-500'">
                {{ comp.points > 0 ? '+' : '' }}{{ comp.points.toFixed(1) }}
              </span>
            </div>
            <div class="text-xs text-gray-500">
              {{ comp.value }} × {{ comp.weight }}
            </div>
          </div>
        </div>
      </div>

      <!-- Metrics Grid -->
      <div class="grid grid-cols-3 gap-4">
        <div class="text-center p-3 bg-blue-50 rounded-lg">
          <div class="text-2xl font-bold text-blue-600">{{ detail.metrics.commits }}</div>
          <div class="text-xs text-gray-500">Commits</div>
        </div>
        <div class="text-center p-3 bg-green-50 rounded-lg">
          <div class="text-2xl font-bold text-green-600">{{ detail.metrics.files_modified }}</div>
          <div class="text-xs text-gray-500">Files Modified</div>
        </div>
        <div class="text-center p-3 bg-purple-50 rounded-lg">
          <div class="text-2xl font-bold text-purple-600">
            {{ formatMinutes(detail.metrics.active_coding_seconds) }}
          </div>
          <div class="text-xs text-gray-500">Active Coding</div>
        </div>
      </div>

      <!-- Time Details -->
      <div class="grid grid-cols-2 gap-4">
        <div class="p-3 bg-gray-50 rounded-lg">
          <div class="text-sm text-gray-500">Work Hours</div>
          <div class="font-medium">
            {{ detail.metrics.start_time || '—' }} - {{ detail.metrics.end_time || '—' }}
          </div>
        </div>
        <div class="p-3 bg-gray-50 rounded-lg">
          <div class="text-sm text-gray-500">Deep Work</div>
          <div class="font-medium">{{ formatMinutes(detail.metrics.deep_work_seconds) }}</div>
        </div>
      </div>

      <!-- Focus & Churn -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <div class="flex justify-between text-sm mb-1">
            <span>Focus Ratio</span>
            <span class="font-medium">{{ (detail.metrics.focus_ratio * 100).toFixed(0) }}%</span>
          </div>
          <ProgressBar :value="detail.metrics.focus_ratio * 100" :showValue="false" />
        </div>
        <div>
          <div class="flex justify-between text-sm mb-1">
            <span>Code Stability</span>
            <span class="font-medium">{{ ((1 - detail.metrics.churn_score) * 100).toFixed(0) }}%</span>
          </div>
          <ProgressBar :value="(1 - detail.metrics.churn_score) * 100" :showValue="false" />
        </div>
      </div>

      <!-- Lines Changed -->
      <div class="p-3 bg-gray-50 rounded-lg">
        <div class="text-sm text-gray-500 mb-2">Lines Changed</div>
        <div class="flex gap-4">
          <span class="text-green-600">+{{ detail.metrics.lines_added }} added</span>
          <span class="text-red-500">-{{ detail.metrics.lines_deleted }} deleted</span>
        </div>
      </div>

      <!-- Languages Chart -->
      <div v-if="detail.wakatime_details?.languages?.length" class="p-4 bg-gray-50 rounded-lg">
        <h4 class="font-semibold text-gray-700 mb-3">Languages</h4>
        <div style="height: 150px;">
          <Doughnut :data="languageChartData" :options="chartOptions" />
        </div>
      </div>

      <!-- Projects -->
      <div v-if="detail.wakatime_details?.projects?.length" class="p-4 bg-gray-50 rounded-lg">
        <h4 class="font-semibold text-gray-700 mb-3">Projects</h4>
        <div class="flex flex-wrap gap-2">
          <Tag v-for="proj in detail.wakatime_details.projects" :key="proj.name" 
               :value="`${proj.name}: ${proj.text}`" severity="info" />
        </div>
      </div>
    </div>
  </Dialog>
</template>
