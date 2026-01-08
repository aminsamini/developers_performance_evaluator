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
import { ShieldCheck, ShieldAlert, Settings } from 'lucide-vue-next'

interface Repository {
    id: number;
    name: string; // owner/repo
    status: 'active' | 'error';
    last_error?: string;
    last_checked?: string;
}

const open = ref(false)
const repositories = ref<Repository[]>([])
const loading = ref(false)
const fixingRepo = ref<Repository | null>(null)
const newToken = ref('')
const updating = ref(false)

const fetchRepositories = async () => {
    loading.value = true
    try {
        const res = await fetch('http://localhost:8000/repositories/')
        if (res.ok) {
            repositories.value = await res.json()
        }
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const openFixDialog = (repo: Repository) => {
    fixingRepo.value = repo
    newToken.value = ''
    // We don't show the old token for security
}

const saveToken = async () => {
    if (!fixingRepo.value || !newToken.value) return;
    
    updating.value = true
    try {
        const res = await fetch(`http://localhost:8000/repositories/${fixingRepo.value.id}/token`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: newToken.value })
        })
        
        if (!res.ok) {
            const err = await res.json()
            alert(`Error: ${err.detail}`)
            return
        }
        
        // Success
        fixingRepo.value = null
        newToken.value = ''
        await fetchRepositories() // Refresh list
    } catch (e) {
        alert("Failed to update token")
    } finally {
        updating.value = false
    }
}

// Fetch on mount (and when dialog opens ideally, but simple for now)
onMounted(() => {
    fetchRepositories()
})
</script>

<template>
  <Dialog v-model:open="open">
    <DialogTrigger as-child>
      <Button variant="outline" class="w-full justify-start">
        <Settings class="mr-2 h-4 w-4" />
        Repositories
      </Button>
    </DialogTrigger>
    <DialogContent class="sm:max-w-[600px]">
      <DialogHeader>
        <DialogTitle>Repository Management</DialogTitle>
        <DialogDescription>
          Manage tracked repositories and update access tokens.
        </DialogDescription>
      </DialogHeader>
      
      <div v-if="loading" class="py-4 text-center">Loading...</div>
      
      <div v-else class="py-4 space-y-4 max-h-[60h] overflow-y-auto">
        <div v-for="repo in repositories" :key="repo.id" 
             class="flex items-center justify-between p-3 border rounded-lg bg-card text-card-foreground shadow-sm">
            <div class="flex flex-col gap-1">
                <div class="flex items-center gap-2 font-medium">
                    {{ repo.name }}
                    <Badge :variant="repo.status === 'error' ? 'destructive' : 'default'" class="text-xs">
                        {{ repo.status }}
                    </Badge>
                </div>
                <div v-if="repo.status === 'error'" class="text-xs text-red-500 font-mono">
                    {{ repo.last_error }}
                </div>
                <div v-else class="text-xs text-muted-foreground">
                    Last checked: {{ repo.last_checked ? new Date(repo.last_checked).toLocaleDateString() : 'Never' }}
                </div>
            </div>
            
            <Button size="sm" :variant="repo.status === 'error' ? 'destructive' : 'secondary'" @click="openFixDialog(repo)">
                {{ repo.status === 'error' ? 'Fix Token' : 'Update Token' }}
            </Button>
        </div>
        
        <div v-if="repositories.length === 0" class="text-center text-muted-foreground italic">
            No repositories found. Add one via the backend API.
        </div>
      </div>
      
      <!-- Nested Dialog Logic (or just inline edit state) -->
      <!-- Simulating a 'sub-view' within the modal for simplicity since nested dialogs can be tricky in Shadcn without proper setup -->
      <div v-if="fixingRepo" class="border-t pt-4 mt-4">
          <h4 class="font-medium mb-2">Update Token for {{ fixingRepo.name }}</h4>
          <div class="flex gap-2">
              <Input v-model="newToken" placeholder="ghp_new_token_here..." type="password" />
              <Button @click="saveToken" :disabled="!newToken || updating">
                  {{ updating ? 'Verifying...' : 'Save' }}
              </Button>
              <Button variant="ghost" @click="fixingRepo = null">Cancel</Button>
          </div>
          <p class="text-xs text-muted-foreground mt-1">
              Validating token immediately. Please ensure it has 'repo' scope.
          </p>
      </div>

    </DialogContent>
  </Dialog>
</template>
