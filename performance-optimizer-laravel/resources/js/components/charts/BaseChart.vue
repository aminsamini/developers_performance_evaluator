<script setup lang="ts">
import { computed } from 'vue';
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  RadialLinearScale,
  Filler
} from 'chart.js';
import { Bar, Doughnut, Line, Pie, Radar, Scatter, PolarArea, Bubble } from 'vue-chartjs';

// Register all necessary components globally for this wrapper
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  PointElement,
  LineElement,
  ArcElement,
  RadialLinearScale,
  Filler
);

const props = defineProps<{
  type: 'line' | 'bar' | 'pie' | 'doughnut' | 'radar' | 'scatter' | 'polarArea' | 'bubble';
  data: any;
  options?: any;
}>();

const chartComponent = computed(() => {
  switch (props.type) {
    case 'bar': return Bar;
    case 'line': return Line;
    case 'pie': return Pie;
    case 'doughnut': return Doughnut;
    case 'radar': return Radar;
    case 'scatter': return Scatter;
    case 'polarArea': return PolarArea;
    case 'bubble': return Bubble;
    default: return Line;
  }
});

const defaultOptions = {
  responsive: true,
  maintainAspectRatio: false,
};

const mergedOptions = computed(() => ({
  ...defaultOptions,
  ...(props.options || {})
}));
</script>

<template>
  <div class="w-full h-full relative">
    <component :is="chartComponent" :data="data" :options="mergedOptions" />
  </div>
</template>
