<script setup lang="ts">
import { ref } from 'vue';
import { API_BASE_URL } from '../config';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Card from 'primevue/card';
import Message from 'primevue/message';

const name = ref('');
const git_username = ref('');
const wakatime_api_key = ref('');
const loading = ref(false);
const message = ref('');
const messageSeverity = ref('info');

const emit = defineEmits(['developerDataChanged']);

const addDeveloper = async () => {
  loading.value = true;
  message.value = '';
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

  try {
    console.log('Sending request to add developer:', { name: name.value, git_username: git_username.value });
    
    const response = await fetch(`${API_BASE_URL}/developers/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: name.value,
        git_username: git_username.value,
        wakatime_api_key: wakatime_api_key.value || null,
      }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);
    console.log('Response received:', response.status);

    if (response.ok) {
      message.value = 'Developer added successfully!';
      messageSeverity.value = 'success';
      name.value = '';
      git_username.value = '';
      wakatime_api_key.value = '';
      emit('developerDataChanged');
    } else {
      const errorText = await response.text();
      message.value = `Error: ${errorText}`;
      messageSeverity.value = 'error';
      console.error('Failed to add developer', errorText);
    }
  } catch (error: any) {
    if (error.name === 'AbortError') {
       message.value = 'Request timed out after 10 seconds. Check Backend.';
    } else {
       message.value = `Network error: ${error}`;
    }
    messageSeverity.value = 'error';
    console.error('Add Developer Error:', error);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <Card class="mb-6">
    <template #title>Add Developer</template>
    <template #content>
      <form @submit.prevent="addDeveloper" class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
            <label for="name">Name</label>
            <InputText id="name" v-model="name" placeholder="John Doe" required />
        </div>
        <div class="flex flex-col gap-2">
            <label for="git_username">GitHub Username</label>
            <InputText id="git_username" v-model="git_username" placeholder="johndoe" required />
        </div>
        <div class="flex flex-col gap-2">
             <label for="wakatime">WakaTime API Key</label>
             <InputText id="wakatime" v-model="wakatime_api_key" placeholder="Optional" />
        </div>
        
        <Button label="Add Developer" type="submit" :loading="loading" icon="pi pi-user-plus" />
        
        <Message v-if="message" :severity="messageSeverity" :closable="false" class="mt-2">{{ message }}</Message>
      </form>
    </template>
  </Card>
</template>
