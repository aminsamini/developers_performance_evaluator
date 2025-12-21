<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { API_BASE_URL } from '../config';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Card from 'primevue/card';
import Message from 'primevue/message';

interface DailyMetric {
  developer: string;
  commits: number;
  coding_time: string;
  score: number;
}

interface DayArchive {
  date: string;
  items: DailyMetric[];
}

const archiveData = ref<DayArchive[]>([]);
const loading = ref(false);
const error = ref('');

const fetchHistory = async () => {
  loading.value = true;
  error.value = '';
  try {
    const response = await fetch(`${API_BASE_URL}/metrics/`);
    if (!response.ok) throw new Error(await response.text());
    archiveData.value = await response.json();
  } catch (err) {
    error.value = `Failed to load history: ${err}`;
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchHistory();
});
</script>

<template>
  <Card class="mt-8">
    <template #title>Activity Archive (Last 30 Days)</template>
    <template #content>
      <div v-if="loading" class="text-center p-4">Loading history...</div>
      <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
      
      <div v-if="!loading && archiveData.length === 0" class="text-center text-gray-500">
        No historical data found.
      </div>

      <div v-for="day in archiveData" :key="day.date" class="mb-6 border-b pb-4 last:border-0">
        <h3 class="text-lg font-semibold text-gray-700 mb-2">{{ day.date }}</h3>
        <DataTable :value="day.items" size="small" stripedRows class="text-sm">
            <Column field="developer" header="Developer"></Column>
            <Column field="commits" header="Commits"></Column>
            <Column field="coding_time" header="Time"></Column>
            <Column field="score" header="Score">
                 <template #body="slotProps">
                    <span class="font-bold text-indigo-600">{{ slotProps.data.score }}</span>
                 </template>
            </Column>
        </DataTable>
      </div>
    </template>
  </Card>
</template>
