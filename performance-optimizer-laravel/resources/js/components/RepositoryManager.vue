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
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Settings, Power, PowerOff, Plus, Pencil, Plug, RefreshCw } from 'lucide-vue-next'
import { useToast } from '@/components/ui/toast/use-toast'
import { API_BASE_URL } from '../config';

interface Repository {
    id: number;
    name: string; // owner/repo
    status: 'active' | 'error' | 'inactive';
    last_error?: string;
    last_checked?: string;
}

const open = ref(false)
const repositories = ref<Repository[]>([])
const loading = ref(false)
const includeInactive = ref(true)
const testingRepoId = ref<number | null>(null)
const { toast } = useToast()

const props = withDefaults(defineProps<{ onOpen?: () => void; hideTrigger?: boolean }>(), { onOpen: undefined, hideTrigger: false });

const openDialog = () => {
  open.value = true;
  setTimeout(() => { props.onOpen?.(); }, 50);
};

defineExpose({ openDialog });

// Create / Edit State
const isCreating = ref(false)
const editingRepo = ref<Repository | null>(null)
const formData = ref({ name: '', token: '' })
const saving = ref(false)

const fetchRepositories = async () => {
    loading.value = true
    try {
        const url = `${API_BASE_URL}/repositories/?include_inactive=${includeInactive.value}`
        const res = await fetch(url)
        if (res.ok) {
            repositories.value = await res.json()
        }
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const startCreate = () => {
    editingRepo.value = null
    isCreating.value = true
    formData.value = { name: '', token: '' }
}

const startEdit = (repo: Repository) => {
    editingRepo.value = repo
    isCreating.value = false
    formData.value = { name: repo.name, token: '' } // Clean token input
}

const cancelEdit = () => {
    editingRepo.value = null
    isCreating.value = false
}

const saveRepository = async () => {
    if (!formData.value.name) return;

    saving.value = true
    try {
        // Create Logic
        if (isCreating.value) {
            const res = await fetch(`${API_BASE_URL}/repositories/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData.value)
            })
            if (!res.ok) throw new Error((await res.json()).detail)
        }
        // Edit Logic (Token Update)
        else if (editingRepo.value) {
             const res = await fetch(`${API_BASE_URL}/repositories/${editingRepo.value.id}/token`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: formData.value.token })
            })
            if (!res.ok) throw new Error((await res.json()).detail)
        }

        cancelEdit()
        fetchRepositories()
    } catch (e: any) {
        alert(e.message || "Failed to save")
    } finally {
        saving.value = false
    }
}

const toggleStatus = async (repo: Repository) => {
    const isActive = repo.status !== 'inactive';
    // const action = isActive ? 'deactivate' : 'activate'
    const confirmMsg = isActive
        ? `Deactivate ${repo.name}? Tracking will stop.`
        : `Activate ${repo.name}? Tracking will resume.`

    if (!confirm(confirmMsg)) return;

    try {
        let url = ''
        let method = ''

        if (isActive) {
            url = `${API_BASE_URL}/repositories/${repo.id}`
            method = 'DELETE'
        } else {
            url = `${API_BASE_URL}/repositories/${repo.id}/activate`
            method = 'POST'
        }

        const res = await fetch(url, { method })
        if (res.ok) {
            fetchRepositories()
        } else {
            alert('Status update failed')
        }
    } catch (e) {
        console.error(e)
    }
}

const testConnection = async (repo: Repository) => {
    testingRepoId.value = repo.id
    try {
        const res = await fetch(`${API_BASE_URL}/repositories/${repo.id}/test`, { method: 'POST' })
        const data = await res.json()
        toast({
            title: data.reachable ? '✅ Connection OK' : '❌ Connection Failed',
            description: data.message,
            variant: data.reachable ? 'default' : 'destructive',
        })
        fetchRepositories()
    } catch (e) {
        toast({ title: 'Error', description: 'Network error during test.', variant: 'destructive' })
    } finally {
        testingRepoId.value = null
    }
}

onMounted(() => {
    fetchRepositories()
})
</script>

<template>
  <Button v-if="!hideTrigger" variant="outline" class="w-full justify-start" @click="openDialog">
    <Settings class="mr-2 h-4 w-4" />
    Repositories
  </Button>
  <Dialog v-model:open="open">
    <DialogContent class="sm:max-w-[700px]">
      <DialogHeader>
        <DialogTitle>Repository Management</DialogTitle>
        <DialogDescription>
          Manage tracked repositories.
        </DialogDescription>
      </DialogHeader>

      <div v-if="!isCreating && !editingRepo">
         <!-- List View -->
          <div class="flex justify-between items-center mb-4">
              <div class="flex items-center space-x-2">
                <Checkbox id="show-inactive-repos" :checked="includeInactive" @update:checked="(v: boolean) => { includeInactive = v; fetchRepositories(); }" />
                <Label for="show-inactive-repos">Show Inactive</Label>
              </div>
              <Button size="sm" @click="startCreate">
                  <Plus class="mr-2 h-4 w-4" /> Add Repository
              </Button>
          </div>

        <div v-if="loading" class="py-4 text-center">Loading...</div>

        <div v-else class="py-2 space-y-2 max-h-[60vh] overflow-y-auto pr-2">
            <div v-for="repo in repositories" :key="repo.id"
                class="flex items-center justify-between p-3 border rounded-lg bg-card"
                :class="{ 'opacity-60 bg-muted': repo.status === 'inactive' }">
                <div class="flex flex-col gap-1">
                    <div class="flex items-center gap-2 font-medium">
                        {{ repo.name }}
                        <Badge v-if="repo.status === 'error'" variant="destructive" class="text-xs">Error</Badge>
                        <Badge v-else-if="repo.status === 'inactive'" variant="secondary" class="text-xs">Inactive</Badge>
                        <Badge v-else variant="outline" class="text-xs text-green-600 border-green-200 bg-green-50">Active</Badge>
                    </div>
                    <div v-if="repo.status === 'error'" class="text-xs text-red-500 font-mono">
                        {{ repo.last_error }}
                    </div>
                    <div v-else class="text-xs text-muted-foreground">
                        Last checked: {{ repo.last_checked ? new Date(repo.last_checked).toLocaleDateString() : 'Never' }}
                    </div>
                </div>

                <div class="flex items-center gap-1">
                    <Button variant="ghost" size="icon" @click="testConnection(repo)" title="Test Connection" :disabled="testingRepoId === repo.id">
                        <Plug v-if="testingRepoId !== repo.id" class="h-4 w-4 text-blue-500" />
                        <RefreshCw v-else class="h-4 w-4 animate-spin text-muted-foreground" />
                    </Button>
                    <Button variant="ghost" size="icon" @click="startEdit(repo)" title="Edit Token">
                        <Pencil class="h-4 w-4 text-primary" />
                    </Button>

                    <Button variant="ghost" size="icon" @click="toggleStatus(repo)" :title="repo.status === 'inactive' ? 'Activate' : 'Deactivate'">
                        <Power v-if="repo.status !== 'inactive'" class="h-4 w-4 text-destructive" />
                        <PowerOff v-else class="h-4 w-4 text-green-600" />
                    </Button>
                </div>
            </div>

            <div v-if="repositories.length === 0" class="text-center text-muted-foreground italic">
                No repositories found. Add one to start tracking.
            </div>
        </div>
      </div>

      <!-- Create / Edit View -->
      <div v-else class="space-y-4">
          <h3 class="font-medium text-lg">{{ isCreating ? 'Add Repository' : 'Edit Repository' }}</h3>

           <div class="grid gap-4 py-4">
              <div v-if="isCreating" class="grid grid-cols-4 items-center gap-4">
                <Label for="repo-name" class="text-right">Name</Label>
                <Input id="repo-name" v-model="formData.name" class="col-span-3" placeholder="owner/repo" />
              </div>
              <div v-else class="grid grid-cols-4 items-center gap-4">
                  <Label class="text-right">Name</Label>
                  <div class="col-span-3 font-medium">{{ formData.name }}</div>
              </div>

              <div class="grid grid-cols-4 items-center gap-4">
                <Label for="token" class="text-right">Token</Label>
                <div class="col-span-3">
                    <Input id="token" v-model="formData.token" type="password" placeholder="ghp_..." />
                    <p class="text-xs text-muted-foreground mt-1" v-if="isCreating">Optional if public</p>
                    <p class="text-xs text-muted-foreground mt-1" v-else>Leave empty to keep existing token</p>
                </div>
              </div>
          </div>

          <DialogFooter>
             <Button variant="outline" @click="cancelEdit">Cancel</Button>
             <Button @click="saveRepository" :disabled="saving">
                 {{ saving ? 'Verifying...' : 'Save' }}
             </Button>
          </DialogFooter>
      </div>

    </DialogContent>
  </Dialog>
</template>
