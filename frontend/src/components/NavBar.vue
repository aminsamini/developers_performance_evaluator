<script setup lang="ts">
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Menu, FileText, Box } from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import ThemeToggle from '@/components/ThemeToggle.vue';
import RepositoryManager from '@/components/RepositoryManager.vue';
import DeveloperManager from '@/components/DeveloperManager.vue';
import TargetedSync from '@/components/TargetedSync.vue';
import ExportModal from '@/components/ExportModal.vue';
import TimezoneSelector from '@/components/TimezoneSelector.vue';
import { useGlobalState } from '@/composables/useGlobalState';

const router = useRouter();
const { developers, selectedTimezone, fetchDevelopers } = useGlobalState();

// Sync Logic (Placeholder for now, will connect to Dashboard logic or make global)
// Since sync logic was in Dashboard, we need a way to trigger it.
// Ideally, the sync function should be global or checking status. 
// For now, we can just toggle the spinner or we need to move the actual sync function to useGlobalState 
// but that function relies on 'summary' ref and toast.
// Strategy: For this iteration, we keep the UI but maybe emit an event or use a global bus?
// Actually simpler: Let's assume syncData is moving to global state too?
// "Sync Data" button in Dashboard called `syncData` which fetched charts.
// If we move the button to NavBar, NavBar needs to trigger Dashboard refresh.
// We can use a global 'triggerSync' ref that Dashboard watches?
// For now, let's keep the UI structure.

// Sync Logic (Placeholder)
// const triggerSync = () => { ... }

onMounted(() => {
    if (developers.value.length === 0) {
        fetchDevelopers();
    }
});
</script>

<template>
  <nav class="fixed top-4 left-4 right-4 z-50 rounded-full border bg-background/80 backdrop-blur-md shadow-sm px-4 py-2 flex items-center justify-between">
    
    <!-- Left: Logo -->
    <div class="flex items-center gap-2 cursor-pointer" @click="router.push('/')">
      <div class="bg-primary/10 p-1.5 rounded-full">
         <Box class="h-5 w-5 text-primary" />
      </div>
      <span class="font-bold text-lg hidden sm:inline-block">Performance Evaluator</span>
    </div>

    <!-- Right: Theme Toggle & Menu -->
    <div class="flex items-center gap-2">
      <ThemeToggle class="rounded-full" />
      
      <Sheet>
        <SheetTrigger as-child>
          <Button variant="ghost" size="icon" class="rounded-full">
            <Menu class="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="right">
          <SheetHeader>
            <SheetTitle>Menu</SheetTitle>
          </SheetHeader>
          <div class="flex flex-col gap-2 mt-8">
             <!-- Navigation & Actions -->
             <RepositoryManager />
             <DeveloperManager />
             <TargetedSync />
             <Button @click="router.push('/reports')" variant="outline" class="w-full justify-start">
                 <FileText class="mr-2 h-4 w-4" />
                 Reports
             </Button>

             <ExportModal :developers="developers" />
             
             <!-- Separator -->
             <div class="h-px bg-border my-2"></div>
             
             <!-- Settings -->
             <TimezoneSelector @update:timezone="(tz: string) => selectedTimezone = tz" class="w-full" />
          </div>
        </SheetContent>
      </Sheet>
    </div>

  </nav>
</template>
