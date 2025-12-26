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

const name = ref('')
const git_username = ref('')
const wakatime_api_key = ref('')
const loading = ref(false)
const message = ref('')

const emit = defineEmits(['developerDataChanged'])

const addDeveloper = async () => {
  loading.value = true
  message.value = ''
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 10000) // 10s timeout

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
  <Dialog>
    <DialogTrigger as-child>
      <Button variant="outline">
        Add Developer
      </Button>
    </DialogTrigger>
    <DialogContent class="sm:max-w-[425px]">
      <DialogHeader>
        <DialogTitle>Add Developer</DialogTitle>
        <DialogDescription>
          Enter the developer's details below. Click save when you're done.
        </DialogDescription>
      </DialogHeader>
      <form @submit.prevent="addDeveloper">
        <div class="grid gap-4 py-4">
          <div class="grid grid-cols-4 items-center gap-4">
            <Label for="name" class="text-right">
              Name
            </Label>
            <Input id="name" v-model="name" class="col-span-3" required />
          </div>
          <div class="grid grid-cols-4 items-center gap-4">
            <Label for="git_username" class="text-right">
              GitHub Username
            </Label>
            <Input id="git_username" v-model="git_username" class="col-span-3" required />
          </div>
          <div class="grid grid-cols-4 items-center gap-4">
            <Label for="wakatime_api_key" class="text-right">
              WakaTime API Key
            </Label>
            <Input id="wakatime_api_key" v-model="wakatime_api_key" class="col-span-3" />
          </div>
        </div>
        <DialogFooter>
          <Button type="submit" :disabled="loading">
            {{ loading ? 'Saving...' : 'Save Changes' }}
          </Button>
        </DialogFooter>
      </form>
       <div v-if="message" class="mt-4 text-center p-2 rounded-md" :class="{ 'bg-green-100 text-green-800': message.includes('successfully'), 'bg-red-100 text-red-800': message.includes('Error') }">
        {{ message }}
      </div>
    </DialogContent>
  </Dialog>
</template>
