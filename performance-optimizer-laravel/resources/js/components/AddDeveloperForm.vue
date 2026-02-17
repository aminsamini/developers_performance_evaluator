<script setup lang="ts">
import { ref } from 'vue'
import { API_BASE_URL } from '../config'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { UserPlus } from 'lucide-vue-next'

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
  <Dialog v-model:open="visible">
    <DialogTrigger as-child>
      <Button variant="default" size="sm">
        <UserPlus class="mr-2 h-4 w-4" /> Add Developer
      </Button>
    </DialogTrigger>
    <DialogContent class="sm:max-w-[425px]">
      <DialogHeader>
        <DialogTitle>Add Developer</DialogTitle>
        <DialogDescription>
          Enter the developer's details below to track their metrics.
        </DialogDescription>
      </DialogHeader>

      <div class="grid gap-4 py-4">
        <div class="grid grid-cols-4 items-center gap-4">
          <Label for="name" class="text-right">Name</Label>
          <Input id="name" v-model="name" class="col-span-3" required />
        </div>
        <div class="grid grid-cols-4 items-center gap-4">
          <Label for="git_username" class="text-right">GitHub</Label>
          <Input id="git_username" v-model="git_username" class="col-span-3" required />
        </div>
        <div class="grid grid-cols-4 items-center gap-4">
          <Label for="wakatime_api_key" class="text-right">WakaTime</Label>
          <Input id="wakatime_api_key" v-model="wakatime_api_key" class="col-span-3" placeholder="Optional" />
        </div>
      </div>

      <div v-if="message" class="mb-4">
         <Alert :variant="message.includes('Error') || message.includes('Network') || message.includes('timed out') ? 'destructive' : 'default'">
           <AlertTitle>{{ message.includes('Error') ? 'Error' : 'Status' }}</AlertTitle>
           <AlertDescription>{{ message }}</AlertDescription>
         </Alert>
      </div>

      <DialogFooter>
         <Button variant="secondary" @click="visible = false">Cancel</Button>
         <Button type="submit" @click="addDeveloper" :disabled="loading">
            <span v-if="loading">Saving...</span>
            <span v-else>Save changes</span>
         </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
