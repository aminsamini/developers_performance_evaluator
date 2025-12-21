<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { API_BASE_URL } from '../config';
import Card from 'primevue/card';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Message from 'primevue/message';

const repoName = ref('');
const repoToken = ref('');
const repositories = ref<any[]>([]);
// Unified state
const loading = ref(false);
const message = ref('');
const messageSeverity = ref('info');

// computed property for validation
const isValidRef = computed(() => {
    if (!repoName.value) return true; // Don't show error while empty
    // Basic regex for owner/repo
    return /^[a-zA-Z0-9-]+\/[a-zA-Z0-9-._]+$/.test(repoName.value);
});

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
    
    // Sanitize Input: Remove "https://github.com/" and ".git"
    let cleanName = repoName.value.trim();
    cleanName = cleanName.replace(/^https?:\/\/github\.com\//, '');
    cleanName = cleanName.replace(/\.git$/, '');
    
    // Simple validation for owner/repo format
    if (!cleanName.includes('/')) {
        message.value = "Invalid format. Use 'owner/repo'.";
        messageSeverity.value = 'error';
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
                token: repoToken.value || null 
            })
        });
        
        if (!res.ok) {
            const errText = await res.text();
             // Try to parse JSON error detail from FastAPI
            try {
                const errJson = JSON.parse(errText);
                throw new Error(errJson.detail || errText);
            } catch (parseErr) {
                throw new Error(errText);
            }
        }
        
        message.value = 'Repository added successfully!';
        messageSeverity.value = 'success';
        repoName.value = '';
        repoToken.value = '';
        await fetchRepositories();
        
    } catch (e: any) {
        console.error(e);
        message.value = `Error: ${e.message}`;
        messageSeverity.value = 'error';
    } finally {
        loading.value = false;
    }
};

onMounted(fetchRepositories);
</script>

<template>
    <Card class="mb-6 h-full">
        <template #title>Repositories</template>
        <template #content>
            <div class="flex flex-col gap-4">
                <div class="flex flex-col gap-2">
                    <InputText v-model="repoName" placeholder="owner/repo (e.g. vuejs/core)" class="w-full" />
                    <InputText v-model="repoToken" placeholder="GitHub Token (Optional - For Private Repos)" class="w-full" type="password" />
                    <Button label="Add Repository" icon="pi pi-plus" @click="addRepository" :loading="loading" class="w-full" />
                </div>
                
                <Message v-if="message" :severity="messageSeverity" :closable="false">{{ message }}</Message>

                <div v-if="repositories.length > 0">
                    <h3 class="text-sm font-semibold mb-2 text-gray-600">Tracked Repositories:</h3>
                    <ul class="list-disc pl-5">
                        <li v-for="repo in repositories" :key="repo.id" class="text-gray-800">{{ repo.name }}</li>
                    </ul>
                </div>
                <div v-else class="text-sm text-gray-500 italic">
                    No repositories added. Global specific commit search will fail without repos.
                </div>
            </div>
        </template>
    </Card>
</template>
