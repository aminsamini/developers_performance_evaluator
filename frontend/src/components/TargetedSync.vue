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
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Calendar } from '@/components/ui/calendar'
import type { DateValue } from '@internationalized/date'

const developers = ref<{ id: number; name: string }[]>([])
const selectedDeveloper = ref<number | null>(null)
const selectedDate = ref<DateValue | null>(null)
const loading = ref(false)
const message = ref('')

const fetchDevelopers = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/developers/`)
    developers.value = await response.json()
  } catch (error) {
    console.error('Failed to fetch developers:', error)
  }
}

const handleSync = async () => {
  loading.value = true
  message.value = ''
  try {
    const response = await fetch(`${API_BASE_URL}/sync/target`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        developer_id: selectedDeveloper.value,
        date: selectedDate.value ? selectedDate.value.toString() : null,
      }),
    })

    if (response.ok) {
      message.value = 'Sync successful!'
    } else {
      const errorText = await response.text()
      message.value = `Error: ${errorText}`
    }
  } catch (error) {
    message.value = 'A network error occurred.'
  } finally {
    loading.value = false
  }
}

const onOpenChange = (isOpen: boolean) => {
  if (isOpen) {
    fetchDevelopers()
  }
}
</script>

<template>
  <Dialog @update:open="onOpenChange">
    <DialogTrigger as-child>
      <Button variant="outline">
        Targeted Sync
      </Button>
    </DialogTrigger>
    <DialogContent class="sm:max-w-[425px]">
      <DialogHeader>
        <DialogTitle>Targeted Sync</DialogTitle>
        <DialogDescription>
          Select a developer and/or a date to sync.
        </DialogDescription>
      </DialogHeader>
      <div class="grid gap-4 py-4">
        <Select v-model="selectedDeveloper">
          <SelectTrigger>
            <SelectValue placeholder="Select a developer" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Developers</SelectLabel>
              <SelectItem v-for="dev in developers" :key="dev.id" :value="dev.id.toString()">
                {{ dev.name }}
              </SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
        <Calendar v-model="selectedDate" />
      </div>
      <DialogFooter>
        <Button @click="handleSync" :disabled="loading">
          {{ loading ? 'Syncing...' : 'Sync' }}
        </Button>
      </DialogFooter>
      <div v-if="message" class="mt-4 text-center p-2 rounded-md" :class="{ 'bg-green-100 text-green-800': message.includes('successful'), 'bg-red-100 text-red-800': message.includes('Error') }">
        {{ message }}
      </div>
    </DialogContent>
  </Dialog>
</template>
