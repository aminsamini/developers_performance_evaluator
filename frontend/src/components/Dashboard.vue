<script setup lang="ts">
import { ref, onMounted } from 'vue';
import AddDeveloperForm from './AddDeveloperForm.vue';
import RepositoryManager from './RepositoryManager.vue';
import ActivityArchive from './ActivityArchive.vue';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import Card from 'primevue/card';
import Message from 'primevue/message';

interface MetricResult {
  developer: string;
  commits: number;
  coding_time: string;
  score: number;
}

const metrics = ref<MetricResult[]>([]);
const loading = ref(false);
const syncMessage = ref('');
const syncSeverity = ref('info');

const syncData = async () => {
  loading.value = true;
  syncMessage.value = 'Syncing...';
  syncSeverity.value = 'info';
  try {
    const response = await fetch('http://127.0.0.1:5000/sync', { method: 'POST' });
    if (response.ok) {
        const data = await response.json();
        metrics.value = data.results;
        syncMessage.value = 'Sync complete!';
        syncSeverity.value = 'success';
    } else {
        const errText = await response.text();
        syncMessage.value = `Sync failed: ${errText}`;
        syncSeverity.value = 'error';
        console.error('Sync failed', errText);
    }
  } catch (error) {
    syncMessage.value = `Network error: ${error}`;
    syncSeverity.value = 'error';
    console.error(error);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="max-w-6xl mx-auto p-4">
    <h1 class="text-3xl font-bold text-center mb-8 text-gray-900">Performance Optimizer</h1>
    
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="md:col-span-1 flex flex-col gap-6">
            <RepositoryManager />
            <AddDeveloperForm @developerDataChanged="syncData" />
        </div>
        
        <div class="md:col-span-2">
            <Card>
                <template #title>
                    <div class="flex justify-between items-center">
                        <span>Contribution Board</span>
                        <Button label="Sync Data" icon="pi pi-refresh" @click="syncData" :loading="loading" severity="success" />
                    </div>
                </template>
                <template #content>
                     <Message v-if="syncMessage" :severity="syncSeverity" :closable="false" class="mb-4">{{ syncMessage }}</Message>

                     <DataTable :value="metrics" tableStyle="min-width: 50rem" stripedRows>
                        <template #empty>No data found. Click "Sync Data" to fetch stats.</template>
                        <Column field="developer" header="Developer" sortable></Column>
                        <Column field="commits" header="Commits" sortable></Column>
                        <Column field="coding_time" header="Time" sortable></Column>
                        <Column field="score" header="Score" sortable>
                            <template #body="slotProps">
                                <span class="font-bold text-indigo-600">{{ slotProps.data.score }}</span>
                            </template>
                        </Column>
                    </DataTable>
                </template>
            </Card>
            
            <ActivityArchive />
        </div>
    </div>
  </div>
</template>
