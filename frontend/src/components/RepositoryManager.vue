<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { API_BASE_URL } from '../config';
import Card from 'primevue/card';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Dialog from 'primevue/dialog';
import Message from 'primevue/message';

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
        <template #title>Repositories</template>
        <template #content>
            <div class="mb-4">
                 <Button label="Add Repository" icon="pi pi-plus" @click="visible = true" size="small" />
            </div>

            <Dialog v-model:visible="visible" header="Add Repository" :modal="true" class="w-full md:w-30rem">
                <span class="p-text-secondary block mb-5">Enter the repository name (owner/repo).</span>
                
                <div class="flex flex-col gap-4 mb-4">
                    <div class="flex flex-col gap-2">
                        <label for="repoName" class="font-semibold text-sm">Repository</label>
                        <InputText id="repoName" v-model="repoName" placeholder="owner/repo" class="w-full" />
                    </div>
                    <div class="flex flex-col gap-2">
                        <label for="repoToken" class="font-semibold text-sm">GitHub Token</label>
                        <InputText id="repoToken" v-model="repoToken" type="password" placeholder="Optional (for private repos)" class="w-full" />
                    </div>
                </div>

                <div v-if="message" class="mb-4">
                     <Message :severity="message.includes('Error') ? 'error' : 'success'" :closable="false">{{ message }}</Message>
                </div>

                <div class="flex justify-end gap-2">
                    <Button label="Cancel" text severity="secondary" @click="visible = false" />
                    <Button label="Add" @click="addRepository" :loading="loading" autofocus />
                </div>
            </Dialog>

            <div v-if="repositories.length > 0">
                <h3 class="text-sm font-semibold mb-2 text-gray-600">Tracked Repositories:</h3>
                <ul class="list-disc pl-5">
                    <li v-for="repo in repositories" :key="repo.id" class="text-gray-800">
                        {{ repo.name }}
                    </li>
                </ul>
            </div>
            <div v-else class="text-sm text-gray-500 italic">
                No repositories added.
            </div>
        </template>
    </Card>
</template>
