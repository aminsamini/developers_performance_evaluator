<script setup lang="ts">
import { ref } from 'vue';
import { API_BASE_URL } from '../config';
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';
import Dropdown from 'primevue/dropdown';
import Calendar from 'primevue/calendar';
import Message from 'primevue/message';

const developers = ref<{ id: number; name: string }[]>([]);
const selectedDeveloper = ref<{ id: number; name: string } | null>(null);
const selectedDate = ref<Date | null>(null);
const loading = ref(false);
const message = ref('');
const visible = ref(false);

const fetchDevelopers = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/developers/`);
    developers.value = await response.json();
  } catch (error) {
    console.error('Failed to fetch developers:', error);
  }
};

const handleSync = async () => {
  loading.value = true;
  message.value = '';
  try {
    const response = await fetch(`${API_BASE_URL}/sync/target`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        developer_id: selectedDeveloper.value ? selectedDeveloper.value.id : null,
        date: selectedDate.value ? selectedDate.value.toISOString().split('T')[0] : null,
      }),
    });

    if (response.ok) {
        message.value = 'Sync successful!';
        // Auto close after success? Maybe wait.
    } else {
      const errorText = await response.text();
      message.value = `Error: ${errorText}`;
    }
  } catch (error) {
    message.value = 'A network error occurred.';
  } finally {
    loading.value = false;
  }
};

const onOpen = () => {
    fetchDevelopers();
};
</script>

<template>
    <div>
        <Button label="Targeted Sync" icon="pi pi-sync" @click="visible = true" severity="secondary" outlined />
        
        <Dialog v-model:visible="visible" header="Targeted Sync" :modal="true" class="w-full md:w-30rem" @show="onOpen">
            <span class="p-text-secondary block mb-5">Select a developer and/or a date to sync manually.</span>
            
            <div class="flex flex-col gap-4 mb-4">
                <div class="flex flex-col gap-2">
                    <label for="dev" class="font-semibold text-sm">Developer</label>
                    <Dropdown id="dev" v-model="selectedDeveloper" :options="developers" optionLabel="name" placeholder="Select a Developer" class="w-full" showClear />
                </div>
                
                <div class="flex flex-col gap-2">
                    <label for="date" class="font-semibold text-sm">Date</label>
                    <Calendar id="date" v-model="selectedDate" showIcon dateFormat="yy-mm-dd" placeholder="Select a specific date (optional)" class="w-full" />
                </div>
            </div>

            <div v-if="message" class="mb-4">
                 <Message :severity="message.includes('Error') ? 'error' : 'success'" :closable="false">{{ message }}</Message>
            </div>

            <div class="flex justify-end gap-2">
                <Button label="Cancel" text severity="secondary" @click="visible = false" />
                <Button label="Sync" @click="handleSync" :loading="loading" autofocus />
            </div>
        </Dialog>
    </div>
</template>
