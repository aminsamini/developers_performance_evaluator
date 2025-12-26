<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { API_BASE_URL } from '../config';
import AddDeveloperForm from './AddDeveloperForm.vue';
import RepositoryManager from './RepositoryManager.vue';
import TargetedSync from './TargetedSync.vue';
import ActivityArchive from './ActivityArchive.vue';
import Button from 'primevue/button';
import Card from 'primevue/card';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Message from 'primevue/message';
import Tag from 'primevue/tag';
import Panel from 'primevue/panel';

interface MetricResult {
  developer: string;
  commits: number;
  coding_time: string;
  score: number;
  start?: string;
  end?: string;
  deep_work?: string;
  focus_ratio?: number;
  switches?: number;
  details?: string; // JSON string
  wakatime_data?: string;
}

const metrics = ref<MetricResult[]>([]);
const loading = ref(false);
const syncMessage = ref('');
const expandedRows = ref([]);

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
  try {
    const response = await fetch(`${API_BASE_URL}/sync`, { method: 'POST' });
    if (response.ok) {
      const data = await response.json();
      metrics.value = data.results;
      syncMessage.value = 'Sync complete!';
    } else {
      const errText = await response.text();
      syncMessage.value = `Sync failed: ${errText}`;
    }
  } catch (error) {
    syncMessage.value = `Network error: ${error}`;
  } finally {
    loading.value = false;
  }
};

onMounted(syncData);
</script>

<template>
  <div class="max-w-6xl mx-auto p-4">
    <h1 class="text-3xl font-bold text-center mb-8 text-gray-900">
      Performance Optimizer
    </h1>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="md:col-span-1 flex flex-col gap-6">
        <RepositoryManager />
        <AddDeveloperForm @developerDataChanged="syncData" />
      </div>

      <div class="md:col-span-2 flex flex-col gap-6">
        <Card>
            <template #title>
                <div class="flex justify-between items-center">
                    <span>Contribution Board</span>
                    <div class="flex gap-2">
                         <Button @click="syncData" :loading="loading" label="Sync Data" icon="pi pi-refresh" size="small" />
                         <TargetedSync />
                    </div>
                </div>
            </template>
            <template #content>
                 <div v-if="syncMessage" class="mb-4">
                     <Message :severity="syncMessage.includes('failed') || syncMessage.includes('error') ? 'error' : 'success'" :closable="false">{{ syncMessage }}</Message>
                 </div>

                 <DataTable v-model:expandedRows="expandedRows" :value="metrics" dataKey="developer" tableStyle="min-width: 50rem">
                    <Column expander style="width: 3rem" />
                    <Column field="developer" header="Developer"></Column>
                    <Column field="commits" header="Commits" sortable></Column>
                    <Column header="Time" sortable field="coding_time">
                        <template #body="slotProps">
                            {{ slotProps.data.coding_time }}
                            <div v-if="slotProps.data.deep_work" class="text-xs text-gray-500">
                                Deep Work: {{ slotProps.data.deep_work }}
                            </div>
                        </template>
                    </Column>
                    <Column field="start" header="Start" sortable>
                        <template #body="slotProps">
                            {{ slotProps.data.start || '-' }}
                        </template>
                    </Column>
                    <Column field="end" header="End" sortable>
                        <template #body="slotProps">
                            {{ slotProps.data.end || '-' }}
                        </template>
                    </Column>
                    <Column field="score" header="Score" sortable>
                        <template #body="slotProps">
                            <Tag :value="slotProps.data.score.toFixed(2)" :severity="slotProps.data.score > 50 ? 'success' : 'warning'" />
                        </template>
                    </Column>

                    <template #expansion="slotProps">
                        <div class="p-4 bg-gray-50">
                            <h4 class="font-bold mb-2">Detailed Productivity Analysis</h4>
                             <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <p><strong>Focus Rate:</strong> {{ (slotProps.data.focus_ratio * 100).toFixed(0) }}%</p>
                                    <p><strong>Context Switches:</strong> {{ slotProps.data.switches }}</p>
                                </div>
                                <div v-if="slotProps.data.details">
                                    <h5 class="text-sm font-semibold mt-2">Top Languages:</h5>
                                    <ul class="list-disc pl-5 text-sm">
                                        <li v-for="lang in getLanguages(slotProps.data.details).slice(0, 3)" :key="lang.name">
                                            {{ lang.name }}: {{ lang.text }} ({{ lang.percent }}%)
                                        </li>
                                    </ul>
                                </div>
                            </div>
                            <!-- Projects Section -->
                             <div v-if="slotProps.data.details" class="mt-2">
                                <h5 class="text-sm font-semibold mt-2">Projects:</h5>
                                <div class="flex flex-wrap gap-2">
                                    <Tag v-for="proj in getProjects(slotProps.data.details)" :key="proj.name" severity="info" :value="proj.name + ': ' + proj.text" />
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
