<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { router } from '@inertiajs/vue3';
import { Menu, FileText, RefreshCw, Box, Settings, Users, Download } from 'lucide-vue-next';
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
import { useToast } from '@/components/ui/toast/use-toast';
import { API_BASE_URL } from '@/config';

const { developers, selectedTimezone, isSyncing, fetchDevelopers, triggerRefresh } = useGlobalState();
const { toast } = useToast();

const menuOpen = ref(false);
const closeMenu = () => { menuOpen.value = false; };

// Modal Refs
const repoManager = ref<any>(null);
const devManager = ref<any>(null);
const syncManager = ref<any>(null);
const exportModal = ref<any>(null);

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

// General Sync Logic
const handleGeneralSync = async () => {
    isSyncing.value = true;
    try {
        const response = await fetch(`${API_BASE_URL}/sync`, { method: 'POST' });
        if (response.ok) {
            const data = await response.json();
            const results = data.results || [];
            const errors = results.filter((r: any) => r.status === 'error');
            const skipped = results.filter((r: any) => r.status === 'skipped');
            const synced = results.filter((r: any) => r.status !== 'error' && r.status !== 'skipped');

            let description = `${synced.length} synced`;
            if (skipped.length > 0) description += `, ${skipped.length} skipped (already up-to-date)`;
            if (errors.length > 0) description += `, ${errors.length} failed`;

            toast({
                title: errors.length > 0 ? "Sync Completed with Errors" : "Sync Complete",
                description,
                variant: errors.length > 0 ? "destructive" : "default",
            });
            triggerRefresh();
        } else {
            const errorText = await response.text();
            toast({
                title: "Sync Failed",
                description: errorText,
                variant: "destructive",
            });
        }
    } catch (err) {
        toast({
            title: "Network Error",
            description: "Could not connect to the backend server.",
            variant: "destructive",
        });
    } finally {
        isSyncing.value = false;
    }
};

onMounted(() => {
    if (developers.value.length === 0) {
        fetchDevelopers();
    }
});
</script>

<template>
  <nav class="fixed top-4 left-4 right-4 z-50 rounded-full border bg-background/80 backdrop-blur-md shadow-sm px-4 py-2 flex items-center justify-between">

    <!-- Left: Logo -->
    <div class="flex items-center gap-2 cursor-pointer" @click="router.get(route('dashboard'))">
      <div class="bg-primary/10 p-1.5 rounded-full">
         <Box class="h-5 w-5 text-primary" />
      </div>
      <span class="font-bold text-lg hidden sm:inline-block">Performance Evaluator</span>
    </div>

    <!-- Right: Theme Toggle & Menu -->
    <div class="flex items-center gap-2">
    
      <ThemeToggle class="rounded-full" />

      <Sheet v-model:open="menuOpen">
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
             <Button variant="outline" class="w-full justify-start" @click="repoManager?.openDialog()">
                 <Settings class="mr-2 h-4 w-4" />
                 Repositories
             </Button>
             <Button variant="outline" class="w-full justify-start" @click="devManager?.openDialog()">
                 <Users class="mr-2 h-4 w-4" />
                 Developers
             </Button>
             <Button variant="outline" class="w-full justify-start" @click="syncManager?.openDialog()">
                 <RefreshCw class="mr-2 h-4 w-4" />
                 Targeted Sync
             </Button>
             <Button @click="closeMenu(); router.get(route('reports'))" variant="outline" class="w-full justify-start">
                 <FileText class="mr-2 h-4 w-4" />
                 Reports
             </Button>
             <Button
                variant="outline"
                class="w-full justify-start"
                @click="closeMenu(); handleGeneralSync()"
                :disabled="isSyncing"
             >
                 <RefreshCw class="mr-2 h-4 w-4" :class="{ 'animate-spin': isSyncing }" />
                 {{ isSyncing ? 'Syncing...' : 'Sync Data' }}
             </Button>
             <Button variant="outline" class="w-full justify-start" @click="exportModal?.openModal()">
                 <Download class="mr-2 h-4 w-4" />
                 Export Report
             </Button>

             <!-- Separator -->
             <div class="h-px bg-border my-2"></div>

             <!-- Settings -->
             <TimezoneSelector @update:timezone="(tz: string) => selectedTimezone = tz" class="w-full" />
          </div>
        </SheetContent>
      </Sheet>
    </div>
  </nav>

  <!-- Modals (Outside nav to not interfere with flex layout) -->
  <RepositoryManager ref="repoManager" :on-open="closeMenu" :hide-trigger="true" />
  <DeveloperManager ref="devManager" :on-open="closeMenu" :hide-trigger="true" />
  <TargetedSync ref="syncManager" :on-open="closeMenu" :hide-trigger="true" />
  <ExportModal ref="exportModal" :developers="developers" :on-open="closeMenu" :hide-trigger="true" />
</template>
