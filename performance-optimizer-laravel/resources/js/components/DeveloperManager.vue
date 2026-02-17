<script setup lang="ts">
import { ref, onMounted } from 'vue'
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
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Users, Pencil, Power, PowerOff, Plus } from 'lucide-vue-next'
import { API_BASE_URL } from '../config';

interface Developer {
    id: number;
    name: string;
    git_username: string | null;
    wakatime_api_key: string | null;
    is_active: boolean;
}

const open = ref(false)
const developers = ref<Developer[]>([])
const loading = ref(false)
const includeInactive = ref(true)

// Edit/Add State
const editingDev = ref<Developer | null>(null)
const isCreating = ref(false)
const formData = ref({
    name: '',
    git_username: '',
    wakatime_api_key: ''
})
const saving = ref(false)

const fetchDevelopers = async () => {
    loading.value = true
    try {
        // We always fetch active ones, but if includeInactive is true, we might need a param
        // Backend `get_developers` supports `include_inactive`
        const url = `${API_BASE_URL}/developers/?include_inactive=${includeInactive.value}`
        const res = await fetch(url)
        if (res.ok) {
            developers.value = await res.json()
        }
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const startCreate = () => {
    editingDev.value = null
    isCreating.value = true
    formData.value = { name: '', git_username: '', wakatime_api_key: '' }
}

const startEdit = (dev: Developer) => {
    editingDev.value = dev
    isCreating.value = false
    formData.value = {
        name: dev.name,
        git_username: dev.git_username || '',
        wakatime_api_key: dev.wakatime_api_key || ''
    }
}

const cancelEdit = () => {
    editingDev.value = null
    isCreating.value = false
}

const saveDeveloper = async () => {
    if (!formData.value.name) return;

    saving.value = true
    try {
        let url = `${API_BASE_URL}/developers/`
        let method = 'POST'

        if (!isCreating.value && editingDev.value) {
            url = `${API_BASE_URL}/developers/${editingDev.value.id}`
            method = 'PUT'
        }

        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData.value)
        })

        if (res.ok) {
            cancelEdit()
            fetchDevelopers()
        } else {
            const err = await res.json()
            alert(`Error: ${err.detail}`)
        }
    } catch (e) {
        alert("Failed to save")
    } finally {
        saving.value = false
    }
}

const toggleStatus = async (dev: Developer) => {
    // const action = dev.is_active ? 'deactivate' : 'activate'
    const confirmMsg = dev.is_active
        ? `Deactivate ${dev.name}? Tracking will stop.`
        : `Activate ${dev.name}? Tracking will resume.`

    if (!confirm(confirmMsg)) return;

    try {
        let url = ''
        let method = ''

        if (dev.is_active) {
            url = `${API_BASE_URL}/developers/${dev.id}`
            method = 'DELETE' // Backend maps DELETE to deactivate
        } else {
            url = `${API_BASE_URL}/developers/${dev.id}/activate`
            method = 'POST'
        }

        const res = await fetch(url, { method })
        if (res.ok) {
            fetchDevelopers()
        } else {
            alert('Status update failed')
        }
    } catch (e) {
        console.error(e)
    }
}

onMounted(() => {
    fetchDevelopers()
})
</script>

<template>
  <Dialog v-model:open="open">
    <DialogTrigger as-child>
      <Button variant="outline" class="w-full justify-start">
        <Users class="mr-2 h-4 w-4" />
        Developers
      </Button>
    </DialogTrigger>
    <DialogContent class="sm:max-w-[700px]">
      <DialogHeader>
        <DialogTitle>Developer Management</DialogTitle>
        <DialogDescription>
          Manage tracked developers. Deactivate developers to stop collecting their metrics.
        </DialogDescription>
      </DialogHeader>

      <div v-if="!isCreating && !editingDev">
          <!-- List View -->
          <div class="flex justify-between items-center mb-4">
              <div class="flex items-center space-x-2">
                <Checkbox id="show-inactive" :checked="includeInactive" @update:checked="(v: boolean) => { includeInactive = v; fetchDevelopers(); }" />
                <Label for="show-inactive">Show Inactive</Label>
              </div>
              <Button size="sm" @click="startCreate">
                  <Plus class="mr-2 h-4 w-4" /> Add Developer
              </Button>
          </div>

          <div v-if="loading" class="text-center py-4">Loading...</div>

          <div v-else class="space-y-2 max-h-[60vh] overflow-y-auto pr-2">
              <div v-for="dev in developers" :key="dev.id"
                   class="flex items-center justify-between p-3 border rounded-lg bg-card"
                   :class="{ 'opacity-60 bg-muted': !dev.is_active }">
                  <div class="flex flex-col">
                      <div class="flex items-center gap-2">
                          <span class="font-medium">{{ dev.name }}</span>
                          <Badge v-if="!dev.is_active" variant="secondary" class="text-xs">Inactive</Badge>
                      </div>
                      <div class="text-xs text-muted-foreground">GitHub: {{ dev.git_username || 'N/A' }}</div>
                  </div>

                  <div class="flex items-center gap-2">
                      <Button variant="ghost" size="icon" @click="startEdit(dev)" title="Edit">
                          <Pencil class="h-4 w-4 text-primary" />
                      </Button>

                      <Button variant="ghost" size="icon" @click="toggleStatus(dev)" :title="dev.is_active ? 'Deactivate' : 'Activate'">
                          <Power v-if="dev.is_active" class="h-4 w-4 text-destructive" />
                          <PowerOff v-else class="h-4 w-4 text-green-600" />
                      </Button>
                  </div>
              </div>
              <div v-if="developers.length === 0" class="text-center text-muted-foreground p-4">
                  No developers found.
              </div>
          </div>
      </div>

      <!-- Create/Edit View -->
      <div v-else class="space-y-4">
          <h3 class="font-medium text-lg">{{ isCreating ? 'Add Developer' : 'Edit Developer' }}</h3>

          <div class="grid gap-4 py-4">
              <div class="grid grid-cols-4 items-center gap-4">
                <Label for="name" class="text-right">Name</Label>
                <Input id="name" v-model="formData.name" class="col-span-3" required />
              </div>
              <div class="grid grid-cols-4 items-center gap-4">
                <Label for="username" class="text-right">Git Username</Label>
                <Input id="username" v-model="formData.git_username" class="col-span-3" placeholder="GitHub username" />
              </div>
              <div class="grid grid-cols-4 items-center gap-4">
                <Label for="wakatime" class="text-right">WakaTime Key</Label>
                <Input id="wakatime" v-model="formData.wakatime_api_key" class="col-span-3" type="password" placeholder="waka_..." />
              </div>
          </div>

          <DialogFooter>
             <Button variant="outline" @click="cancelEdit">Cancel</Button>
             <Button @click="saveDeveloper" :disabled="saving">
                 {{ saving ? 'Saving...' : 'Save' }}
             </Button>
          </DialogFooter>
      </div>

    </DialogContent>
  </Dialog>
</template>
