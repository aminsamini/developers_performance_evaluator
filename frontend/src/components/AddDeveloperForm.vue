<script setup lang="ts">
import { ref } from 'vue'
import { API_BASE_URL } from '../config'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'

const name = ref('')
const git_username = ref('')
const wakatime_api_key = ref('')
const loading = ref(false)
const message = ref('')
const visible = ref(false) // Toggle for Dialog

const emit = defineEmits(['developerDataChanged'])

const addDeveloper = async () => {
  loading.value = true
  message.value = ''
  
  // Use AbortController for timeout
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 10000) // 10s

  try {
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
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (response.ok) {
      message.value = 'Developer added successfully!'
      name.value = ''
      git_username.value = ''
      wakatime_api_key.value = ''
      emit('developerDataChanged')
      // Optional: visible.value = false;
    } else {
      const errorText = await response.text()
      message.value = `Error: ${errorText}`
    }
  } catch (error: any) {
    if (error.name === 'AbortError') {
      message.value = 'Request timed out after 10 seconds. Check Backend.'
    } else {
      message.value = `Network error: ${error}`
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <Button label="Add Developer" icon="pi pi-user-plus" @click="visible = true" size="small" />

    <Dialog v-model:visible="visible" header="Add Developer" :modal="true" class="w-full md:w-30rem">
        <span class="p-text-secondary block mb-5">Enter the developer's details below.</span>
        
        <div class="flex flex-col gap-4 mb-4">
            <div class="flex flex-col gap-2">
                <label for="name" class="font-semibold text-sm">Name</label>
                <InputText id="name" v-model="name" class="w-full" required />
            </div>
            
            <div class="flex flex-col gap-2">
                <label for="git_username" class="font-semibold text-sm">GitHub Username</label>
                <InputText id="git_username" v-model="git_username" class="w-full" required />
            </div>
            
            <div class="flex flex-col gap-2">
                <label for="wakatime_api_key" class="font-semibold text-sm">WakaTime API Key</label>
                <InputText id="wakatime_api_key" v-model="wakatime_api_key" class="w-full" placeholder="Optional" />
            </div>
        </div>
        
        <div v-if="message" class="mb-4">
             <Message :severity="message.includes('Error') || message.includes('Network') ? 'error' : 'success'" :closable="false">{{ message }}</Message>
        </div>

        <div class="flex justify-end gap-2">
            <Button label="Cancel" text severity="secondary" @click="visible = false" />
            <Button label="Save" @click="addDeveloper" :loading="loading" autofocus />
        </div>
    </Dialog>
  </div>
</template>
