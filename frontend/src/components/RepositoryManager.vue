<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { API_BASE_URL } from '../config';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Plus, GitBranch, Users } from 'lucide-vue-next'
import AddDeveloperForm from './AddDeveloperForm.vue';

const emit = defineEmits(['dataUpdated']);

// Repository State
const repoName = ref('');
const repoToken = ref('');
const repositories = ref<any[]>([]);
const repoLoading = ref(false);
const repoMessage = ref('');
const repoDialogVisible = ref(false);

// Developer State
const developers = ref<any[]>([]);

// Fetch Data
const fetchRepositories = async () => {
    try {
        const res = await fetch(`${API_BASE_URL}/repositories/`);
        repositories.value = await res.json();
    } catch (e) {
        console.error(e);
    }
};

const fetchDevelopers = async () => {
    try {
        const res = await fetch(`${API_BASE_URL}/developers/`);
        developers.value = await res.json();
    } catch (e) {
        console.error(e);
    }
};

const handleDevAdded = () => {
    fetchDevelopers();
    emit('dataUpdated');
};

const addRepository = async () => {
    if (!repoName.value) return;

    let cleanName = repoName.value.trim();
    cleanName = cleanName.replace(/^https?:\/\/github\.com\//, '');
    cleanName = cleanName.replace(/\.git$/, '');

    if (!cleanName.includes('/')) {
        repoMessage.value = "Invalid format. Use 'owner/repo'.";
        return;
    }

    repoLoading.value = true;
    repoMessage.value = '';

    try {
        const res = await fetch(`${API_BASE_URL}/repositories/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: cleanName,
                token: repoToken.value || null,
            }),
        });

        if (!res.ok) {
            const errText = await res.text();
            try {
                const errJson = JSON.parse(errText);
                throw new Error(errJson.detail || errText);
            } catch (parseErr) {
                throw new Error(errText);
            }
        }

        repoMessage.value = 'Repository added successfully!';
        repoName.value = '';
        repoToken.value = '';
        await fetchRepositories();
        emit('dataUpdated');
    } catch (e: any) {
        console.error(e);
        repoMessage.value = `Error: ${e.message}`;
    } finally {
        repoLoading.value = false;
    }
};

onMounted(() => {
    fetchRepositories();
    fetchDevelopers();
});
</script>

<template>
    <Card class="h-full">
        <CardHeader class="pb-3">
            <CardTitle class="text-xl font-bold flex items-center gap-2">
                Settings
            </CardTitle>
            <CardDescription>Manage team members and tracked repositories</CardDescription>
        </CardHeader>
        <CardContent class="grid gap-6">
            
            <!-- Developers Section -->
            <div>
                <div class="flex items-center justify-between mb-3">
                    <h3 class="font-semibold text-sm flex items-center gap-2">
                        <Users class="w-4 h-4" /> Developers
                    </h3>
                    <AddDeveloperForm @developerDataChanged="handleDevAdded" />
                </div>
                
                <div class="bg-muted/30 rounded-lg p-2 max-h-40 overflow-y-auto">
                    <div v-if="developers.length > 0" class="space-y-1">
                        <div v-for="dev in developers" :key="dev.id" class="text-sm px-2 py-1 bg-background rounded border flex justify-between items-center">
                            <span class="font-medium">{{ dev.name }}</span>
                            <!-- <span class="text-xs text-muted-foreground">{{ dev.git_username }}</span> -->
                        </div>
                    </div>
                     <div v-else class="text-sm text-muted-foreground italic text-center py-2">
                        No developers added.
                    </div>
                </div>
            </div>

            <div class="border-t"></div>

            <!-- Repositories Section -->
            <div>
                <div class="flex items-center justify-between mb-3">
                    <h3 class="font-semibold text-sm flex items-center gap-2">
                         <GitBranch class="w-4 h-4" /> Repositories
                    </h3>
                    <Dialog v-model:open="repoDialogVisible">
                        <DialogTrigger as-child>
                            <Button size="sm" variant="outline">
                                <Plus class="mr-2 h-4 w-4" /> Add Repo
                            </Button>
                        </DialogTrigger>
                        <DialogContent class="sm:max-w-[425px]">
                            <DialogHeader>
                                <DialogTitle>Add Repository</DialogTitle>
                                <DialogDescription>
                                     Enter the repository name (owner/repo).
                                </DialogDescription>
                            </DialogHeader>

                            <div class="grid gap-4 py-4">
                                <div class="grid grid-cols-4 items-center gap-4">
                                    <Label for="repoName" class="text-right">Repository</Label>
                                    <Input id="repoName" v-model="repoName" placeholder="owner/repo" class="col-span-3" />
                                </div>
                                <div class="grid grid-cols-4 items-center gap-4">
                                    <Label for="repoToken" class="text-right">Token</Label>
                                    <Input id="repoToken" type="password" v-model="repoToken" placeholder="Optional (private)" class="col-span-3" />
                                </div>
                            </div>

                            <div v-if="repoMessage" class="mb-4">
                                <Alert :variant="repoMessage.includes('Error') ? 'destructive' : 'default'">
                                    <AlertTitle>{{ repoMessage.includes('Error') ? 'Error' : 'Status' }}</AlertTitle>
                                    <AlertDescription>{{ repoMessage }}</AlertDescription>
                                </Alert>
                            </div>

                            <DialogFooter>
                                <Button variant="secondary" @click="repoDialogVisible = false">Cancel</Button>
                                <Button @click="addRepository" :loading="repoLoading">Add</Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </div>

                <div class="bg-muted/30 rounded-lg p-2 max-h-40 overflow-y-auto">
                     <div v-if="repositories.length > 0" class="space-y-1">
                        <div v-for="repo in repositories" :key="repo.id" class="text-sm px-2 py-1 bg-background rounded border">
                            {{ repo.name }}
                        </div>
                    </div>
                    <div v-else class="text-sm text-muted-foreground italic text-center py-2">
                        No repositories added.
                    </div>
                </div>
            </div>

        </CardContent>
    </Card>
</template>
