<script setup lang="ts">
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Maximize2 } from 'lucide-vue-next';
import BaseChart from '@/components/charts/BaseChart.vue';

defineProps<{
  title: string;
  chartType: string;
  chartData: any;
  chartOptions?: any;
}>();

defineEmits(['expand']);
</script>

<template>
  <Card class="group relative overflow-hidden transition-all hover:shadow-md h-[300px] flex flex-col">
    <CardHeader class="p-4 pb-2">
      <CardTitle class="text-sm font-medium text-muted-foreground truncate" :title="title">
        {{ title }}
      </CardTitle>
    </CardHeader>
    <CardContent class="flex-1 p-4 pt-0 min-h-0 relative">
      <BaseChart :type="chartType as any" :data="chartData" :options="chartOptions" />
      
      <!-- Overlay -->
      <div class="absolute inset-0 bg-background/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-[1px] cursor-pointer" @click="$emit('expand')">
        <Button variant="secondary" size="sm" class="pointer-events-none">
          <Maximize2 class="h-4 w-4 mr-2" />
          Expand Details
        </Button>
      </div>
    </CardContent>
  </Card>
</template>
