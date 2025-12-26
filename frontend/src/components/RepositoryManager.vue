<script setup lang="ts">
import { ref, onMounted } from 'vue'
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
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'


const repoName = ref('')
const repoToken = ref('')
const repositories = ref<any[]>([])
const loading = ref(false)
const message = ref('')

const fetchRepositories = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/repositories/`)
    repositories.value = await res.json()
  } catch (e) {
    console.error(e)
  }
}

const addRepository = async () => {
  if (!repoName.value) return

  let cleanName = repoName.value.trim()
  cleanName = cleanName.replace(/^https?:\/\/github\.com\//, '')
  cleanName = cleanName.replace(/\.git$/, '')

  if (!cleanName.includes('/')) {
    message.value = "Invalid format. Use 'owner/repo'."
    return
  }

  loading.value = true
  message.value = ''

  try {
    const res = await fetch(`${API_BASE_URL}/repositories/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: cleanName,
        token: repoToken.value || null,
      }),
    })

    if (!res.ok) {
      const errText = await res.text()
      try {
        const errJson = JSON.parse(errText)
        throw new Error(errJson.detail || errText)
      } catch (parseErr) {
        throw new Error(errText)
      }
    }

    message.value = 'Repository added successfully!'
    repoName.value = ''
    repoToken.value = ''
    await fetchRepositories()
  } catch (e: any) {
    console.error(e)
    message.value = `Error: ${e.message}`
  } finally {
    loading.value = false
  }
}

onMounted(fetchRepositories)
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>Repositories</CardTitle>
    </CardHeader>
    <CardContent>
      <Dialog>
        <DialogTrigger as-child>
          <Button variant="outline">
            Add Repository
          </Button>
        </DialogTrigger>
        <DialogContent class="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Add Repository</DialogTitle>
            <DialogDescription>
              Enter the repository details below. Provide a token for private repositories.
            </DialogDescription>
          </DialogHeader>
          <form @submit.prevent="addRepository">
            <div class="grid gap-4 py-4">
              <div class="grid grid-cols-4 items-center gap-4">
                <Label for="repoName" class="text-right">
                  Repository
                </Label>
                <Input id="repoName" v-model="repoName" class="col-span-3" placeholder="owner/repo" required />
              </div>
              <div class="grid grid-cols-4 items-center gap-4">
                <Label for="repoToken" class="text-right">
                  GitHub Token
                </Label>
                <Input id="repoToken" v-model="repoToken" type="password" class="col-span-3" placeholder="Optional" />
              </div>
            </div>
            <DialogFooter>
              <Button type="submit" :disabled="loading">
                {{ loading ? 'Adding...' : 'Add Repository' }}
              </Button>
            </DialogFooter>
          </form>
           <div v-if="message" class="mt-4 text-center p-2 rounded-md" :class="{ 'bg-green-100 text-green-800': message.includes('successfully'), 'bg-red-100 text-red-800': message.includes('Error') }">
            {{ message }}
          </div>
        </DialogContent>
      </Dialog>
      <div v-if="repositories.length > 0" class="mt-4">
        <h3 class="text-sm font-semibold mb-2 text-gray-600">
          Tracked Repositories:
        </h3>
        <ul class="list-disc pl-5">
          <li v-for="repo in repositories" :key="repo.id" class="text-gray-800">
            {{ repo.name }}
          </li>
        </ul>
      </div>
      <div v-else class="mt-4 text-sm text-gray-500 italic">
        No repositories added.
      </div>
    </CardContent>
  </Card>
</template>
