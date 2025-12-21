<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { API_BASE_URL } from '../config';
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
  deep_work?: string;
  focus_ratio?: number;
  switches?: number;
  details?: string;
}

const metrics = ref<MetricResult[]>([]);
const loading = ref(false);
const syncMessage = ref('');
const syncSeverity = ref('info');
const expandedRows = ref({});

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

const syncData = async () => {
  loading.value = true;
  syncMessage.value = 'Syncing...';
  syncSeverity.value = 'info';
  try {
    const response = await fetch(`${API_BASE_URL}/sync`, { method: 'POST' });
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
                        <div class="flex gap-2">
                             <Button label="Sync Data" icon="pi pi-refresh" @click="syncData" :loading="loading" severity="success" />
                        </div>
                    </div>
                </template>
                <template #content>
                     <Message v-if="syncMessage" :severity="syncSeverity" :closable="false" class="mb-4">{{ syncMessage }}</Message>

                     <DataTable :value="metrics" v-model:expandedRows="expandedRows" dataKey="developer" tableStyle="min-width: 50rem" stripedRows>
                         <template #empty>No data found. Click "Sync Data" to fetch stats.</template>
                        
                        <Column expander style="width: 3rem" />
                        <Column field="developer" header="Developer" sortable></Column>
                        <Column field="commits" header="Commits" sortable></Column>
                        <Column field="coding_time" header="Time" sortable>
                             <template #body="slotProps">
                                {{ slotProps.data.coding_time }}
                                <div class="text-xs text-gray-500">Deep Work: {{ slotProps.data.deep_work }}</div>
                             </template>
                        </Column>
                        <Column field="score" header="Score" sortable>
                            <template #body="slotProps">
                                <span class="font-bold text-indigo-600 text-lg">{{ slotProps.data.score }}</span>
                            </template>
                        </Column>

                        <template #expansion="slotProps">
                            <div class="p-4 bg-gray-50 border-t">
                                <h4 class="font-bold mb-2">Detailed Productivity Analysis</h4>
                                <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                                     <div class="bg-white p-3 rounded shadow-sm">
                                         <div class="text-xs text-gray-500 uppercase">Focus Rate</div>
                                         <div class="font-bold text-xl">{{ (slotProps.data.focus_ratio * 100).toFixed(0) }}%</div>
                                         <div class="text-xs text-gray-400">Time on Main Project</div>
                                     </div>
                                     <div class="bg-white p-3 rounded shadow-sm">
                                         <div class="text-xs text-gray-500 uppercase">Context Switches</div>
                                         <div class="font-bold text-xl text-red-500">{{ slotProps.data.switches }}</div>
                                         <div class="text-xs text-gray-400">Task Interruptions</div>
                                     </div>
                                     <div class="bg-white p-3 rounded shadow-sm">
                                         <div class="text-xs text-gray-500 uppercase">Deep Work</div>
                                         <div class="font-bold text-xl text-green-600">{{ slotProps.data.deep_work }}</div>
                                         <div class="text-xs text-gray-400">Sessions > 1hr</div>
                                     </div>
                                </div>
                                
                                <div v-if="slotProps.data.details" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <h5 class="text-sm font-semibold mb-2">Projects</h5>
                                        <div class="flex flex-wrap gap-2">
                                            <span v-for="proj in getProjects(slotProps.data.details)" :key="proj.name" 
                                                  class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                                                {{ proj.name }} ({{ proj.text }})
                                            </span>
                                        </div>
                                    </div>
                                    <div>
                                        <h5 class="text-sm font-semibold mb-2">Languages & Tools</h5>
                                        <div class="flex flex-wrap gap-2">
                                            <span v-for="lang in getLanguages(slotProps.data.details)" :key="lang.name" 
                                                  class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                                                {{ lang.name }} ({{ lang.text }})
                                            </span>
                                        </div>
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
