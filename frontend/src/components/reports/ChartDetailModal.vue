<script setup lang="ts">
import { ref, computed } from 'vue';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import BaseChart from '@/components/charts/BaseChart.vue';

const props = defineProps<{
  isOpen: boolean;
  title: string;
  chartType: string;
  rawData: any; // The raw list (e.g. languages array) to process
  computedData?: any; // Pre-computed Chart.js data object (overrides raw processing)
  category: 'time' | 'language' | 'project' | 'editor'; // Context for processing
}>();

const emit = defineEmits(['update:isOpen']);

// Local Filters
const topN = ref(10);
const showLegend = ref(true);

const processedData = computed(() => {
    // If pre-computed data is provided, use it directly (bypassing local processing)
    if (props.computedData) {
        return props.computedData;
    }

    if (!props.rawData) return null;
    let data = [...props.rawData];
    
    // Sort descending by total_seconds if applicable
    if (data.length > 0 && data[0].total_seconds !== undefined) {
        data.sort((a: any, b: any) => b.total_seconds - a.total_seconds);
    }

    // Apply Top N
    const sliced = data.slice(0, topN.value);
    
    // Generate Chart Data Structure
    const labels = sliced.map((d: any) => d.name || d.date);
    const values = sliced.map((d: any) => (d.total_seconds / 3600).toFixed(2));
    
    // Colors
    const palette = [
        '#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ec4899', 
        '#ef4444', '#06b6d4', '#84cc16', '#6366f1', '#a855f7'
    ];

    let dataset: any = {
        label: props.title,
        data: values,
        backgroundColor: props.chartType === 'line' ? 'rgba(59, 130, 246, 0.1)' : palette,
        borderColor: props.chartType === 'line' ? '#3b82f6' : '#ffffff',
        borderWidth: 1,
        fill: props.chartType === 'line'
    };
    
    if (props.chartType === 'bar' && props.category !== 'time') {
         // Single color for normal bars, multi for distribution
         dataset.backgroundColor = palette;
    }

    return {
        labels,
        datasets: [dataset]
    };
});

const chartOptions = computed(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { 
            display: showLegend.value,
            position: 'right'
        }
    }
}));

</script>

<template>
  <Dialog :open="isOpen" @update:open="(val) => emit('update:isOpen', val)">
    <DialogContent class="max-w-4xl h-[80vh] flex flex-col">
      <DialogHeader>
        <DialogTitle>{{ title }}</DialogTitle>
        <DialogDescription>Detailed view and customization.</DialogDescription>
      </DialogHeader>
      
      <!-- Toolbar -->
      <div class="flex items-center gap-4 py-2 border-b">
         <div class="flex items-center gap-2">
            <span class="text-sm">Items to show:</span>
            <select v-model="topN" class="h-8 rounded border px-2 text-sm">
                <option :value="5">Top 5</option>
                <option :value="10">Top 10</option>
                <option :value="20">Top 20</option>
                <option :value="1000">All</option>
            </select>
         </div>
         <div class="flex items-center gap-2">
             <input type="checkbox" id="showLegend" v-model="showLegend" class="rounded border-gray-300" />
             <label for="showLegend" class="text-sm">Show Legend</label>
         </div>
      </div>

      <!-- Chart Area -->
      <div class="flex-1 min-h-0 relative p-4">
         <BaseChart v-if="processedData" :type="chartType as any" :data="processedData" :options="chartOptions" />
      </div>

    </DialogContent>
  </Dialog>
</template>
