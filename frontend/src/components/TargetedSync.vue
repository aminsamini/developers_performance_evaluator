<script setup lang="ts">
import { ref, watch } from 'vue';
import { API_BASE_URL } from '../config';
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
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { RefreshCw } from 'lucide-vue-next'

const developers = ref<{ id: number; name: string }[]>([]);
const selectedDeveloper = ref<{ id: number; name: string } | null>(null);
const selectedDate = ref<Date | null>(null);
const loading = ref(false);
const message = ref('');
const visible = ref(false);
const selectedDeveloperName = ref<string>('');

const onDeveloperSelect = (name: string) => {
  const dev = developers.value.find((d) => d.name === name);
  selectedDeveloper.value = dev || null;
};



const fetchDevelopers = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/developers/`);
    developers.value = await response.json();
  } catch (error) {
    console.error('Failed to fetch developers:', error);
  }
};

const handleSync = async () => {
  loading.value = true;
  message.value = '';
  try {
    const response = await fetch(`${API_BASE_URL}/sync/target`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        developer_id: selectedDeveloper.value ? selectedDeveloper.value.id : null,
        date: selectedDate.value ? selectedDate.value.toISOString().split('T')[0] : null,
      }),
    });

    if (response.ok) {
        message.value = 'Sync successful!';
        // Auto close after success? Maybe wait.
    } else {
      const errorText = await response.text();
      message.value = `Error: ${errorText}`;
    }
  } catch (error) {
    message.value = 'A network error occurred.';
  } finally {
    loading.value = false;
  }
};

watch(visible, (isOpen) => {
  if (isOpen) {
    fetchDevelopers();
  }
});
</script>

<template>
  <Dialog v-model:open="visible">
    <DialogTrigger as-child>
      <Button variant="outline" size="default">
        <RefreshCw class="mr-2 h-4 w-4" /> Targeted Sync
      </Button>
    </DialogTrigger>
    <DialogContent class="sm:max-w-[425px]">
      <DialogHeader>
        <DialogTitle>Targeted Sync</DialogTitle>
        <DialogDescription>
          Select a developer and/or a date to sync manually.
        </DialogDescription>
      </DialogHeader>

      <div class="grid gap-4 py-4">
        <div class="grid flex-col gap-2">
           <Label for="dev">Developer</Label>
           <Select v-model="selectedDeveloperName" @update:modelValue="onDeveloperSelect">
              <SelectTrigger>
                <SelectValue placeholder="Select a Developer" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem v-for="dev in developers" :key="dev.id" :value="dev.name">
                  {{ dev.name }}
                </SelectItem>
              </SelectContent>
           </Select>
        </div>

        <div class="grid flex-col gap-2">
           <Label for="date">Date</Label>
           <!-- Native Date Input styled with Shadcn Input class for theme support -->
           <Input 
             id="date" 
             type="date" 
             :value="selectedDate ? selectedDate.toISOString().split('T')[0] : ''"
             @input="(e: any) => selectedDate = e.target.value ? new Date(e.target.value) : null"
           />
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
         <Button @click="handleSync" :disabled="loading">
            <span v-if="loading">Syncing...</span>
            <span v-else>Sync</span>
         </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
