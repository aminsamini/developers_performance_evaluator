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
import { Plus } from 'lucide-vue-next'

const repoName = ref('');
const repoToken = ref('');
const repositories = ref<any[]>([]);
const loading = ref(false);
const message = ref('');
const visible = ref(false); // Controls Dialog visibility

const fetchRepositories = async () => {
    try {
        const res = await fetch(`${API_BASE_URL}/repositories/`);
        repositories.value = await res.json();
    } catch (e) {
        console.error(e);
    }
};

const addRepository = async () => {
    if (!repoName.value) return;

    let cleanName = repoName.value.trim();
    cleanName = cleanName.replace(/^https?:\/\/github\.com\//, '');
    cleanName = cleanName.replace(/\.git$/, '');

    if (!cleanName.includes('/')) {
        message.value = "Invalid format. Use 'owner/repo'.";
        return;
    }

    loading.value = true;
    message.value = '';

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

        message.value = 'Repository added successfully!';
        repoName.value = '';
        repoToken.value = '';
        await fetchRepositories();
        // Option: visible.value = false; // Auto close?
    } catch (e: any) {
        console.error(e);
        message.value = `Error: ${e.message}`;
    } finally {
        loading.value = false;
    }
};

onMounted(fetchRepositories);
</script>

<template>
    <Card class="h-full">
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-lg font-bold">Repositories</CardTitle>
            <Dialog v-model:open="visible">
                <DialogTrigger as-child>
                    <Button size="sm">
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

                    <div v-if="message" class="mb-4">
                        <Alert :variant="message.includes('Error') ? 'destructive' : 'default'">
                            <AlertTitle>{{ message.includes('Error') ? 'Error' : 'Status' }}</AlertTitle>
                            <AlertDescription>{{ message }}</AlertDescription>
                        </Alert>
                    </div>

                    <DialogFooter>
                        <Button variant="secondary" @click="visible = false">Cancel</Button>
                        <Button @click="addRepository" :loading="loading">Add</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </CardHeader>
        <CardContent>
            <div v-if="repositories.length > 0">
                <h3 class="text-sm font-semibold mb-2 text-muted-foreground">Tracked Repositories:</h3>
                <ul class="list-disc pl-5">
                    <li v-for="repo in repositories" :key="repo.id" class="text-sm">
                        {{ repo.name }}
                    </li>
                </ul>
            </div>
            <div v-else class="text-sm text-muted-foreground italic">
                No repositories added.
            </div>
        </CardContent>
    </Card>
</template>
