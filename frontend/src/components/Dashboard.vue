<script setup lang="ts">
import { ref } from 'vue'
import { API_BASE_URL } from '../config'
import AddDeveloperForm from './AddDeveloperForm.vue'
import RepositoryManager from './RepositoryManager.vue'
import TargetedSync from './TargetedSync.vue'
import ActivityArchive from './ActivityArchive.vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'

interface MetricResult {
  developer: string
  commits: number
  coding_time: string
  score: number
  deep_work?: string
  focus_ratio?: number
  switches?: number
  details?: string
}

const metrics = ref<MetricResult[]>([])
const loading = ref(false)
const syncMessage = ref('')

const getLanguages = (jsonStr: string) => {
  try {
    const data = JSON.parse(jsonStr)
    return data.languages || []
  } catch (e) {
    return []
  }
}

const getProjects = (jsonStr: string) => {
  try {
    const data = JSON.parse(jsonStr)
    return data.projects || []
  } catch (e) {
    return []
  }
}

const syncData = async () => {
  loading.value = true
  syncMessage.value = 'Syncing...'
  try {
    const response = await fetch(`${API_BASE_URL}/sync`, { method: 'POST' })
    if (response.ok) {
      const data = await response.json()
      metrics.value = data.results
      syncMessage.value = 'Sync complete!'
    } else {
      const errText = await response.text()
      syncMessage.value = `Sync failed: ${errText}`
    }
  } catch (error) {
    syncMessage.value = `Network error: ${error}`
  } finally {
    loading.value = false
  }
}
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

      <div class="md-col-span-2">
        <Card>
          <CardHeader>
            <div class="flex justify-between items-center">
              <CardTitle>Contribution Board</CardTitle>
              <div class="flex gap-2">
                <Button @click="syncData" :disabled="loading">
                  {{ loading ? 'Syncing...' : 'Sync Data' }}
                </Button>
                <TargetedSync />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div v-if="syncMessage" class="mb-4 text-center p-2 rounded-md" :class="{ 'bg-green-100 text-green-800': syncMessage.includes('complete'), 'bg-red-100 text-red-800': syncMessage.includes('failed') }">
              {{ syncMessage }}
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead />
                  <TableHead>Developer</TableHead>
                  <TableHead>Commits</TableHead>
                  <TableHead>Time</TableHead>
                  <TableHead>Score</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <template v-for="metric in metrics" :key="metric.developer">
                  <Collapsible as="tr">
                    <CollapsibleTrigger as-child>
                      <TableRow>
                        <TableCell>
                          <Button variant="ghost" size="sm">
                            <span class="i-radix-icons-caret-down" />
                          </Button>
                        </TableCell>
                        <TableCell>{{ metric.developer }}</TableCell>
                        <TableCell>{{ metric.commits }}</TableCell>
                        <TableCell>
                          {{ metric.coding_time }}
                          <div class="text-xs text-gray-500">
                            Deep Work: {{ metric.deep_work }}
                          </div>
                        </TableCell>
                        <TableCell>{{ metric.score }}</TableCell>
                      </TableRow>
                    </CollapsibleTrigger>
                    <CollapsibleContent as="tr">
                      <TableCell :colspan="5">
                        <div class="p-4 bg-gray-50 border-t">
                          <h4 class="font-bold mb-2">
                            Detailed Productivity Analysis
                          </h4>
                          <!-- Details -->
                        </div>
                      </TableCell>
                    </CollapsibleContent>
                  </Collapsible>
                </template>
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <ActivityArchive />
      </div>
    </div>
  </div>
</template>
