<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { ChevronLeft, ChevronRight } from 'lucide-vue-next';
import { API_BASE_URL } from '../config';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button';
import DeveloperDayDetail from './DeveloperDayDetail.vue';

interface DailyMetric {
    developer: string;
    developer_id?: number;
    commits: number;
    coding_time: string;
    start?: string;
    end?: string;
    score: number;
    churn_score?: number;
}

interface DayArchive {
    date: string;
    items: DailyMetric[];
}

interface Pagination {
    page: number;
    per_page: number;
    total_days: number;
    total_pages: number;
}

const archiveData = ref<DayArchive[]>([]);
const pagination = ref<Pagination>({ page: 1, per_page: 7, total_days: 0, total_pages: 1 });
const loading = ref(false);
const error = ref('');

// Detail modal state
const detailVisible = ref(false);
const selectedDeveloperId = ref<number | null>(null);
const selectedDeveloperName = ref('');
const selectedDate = ref('');

const fetchHistory = async (page: number = 1) => {
    loading.value = true;
    error.value = '';
    try {
        let url = `${API_BASE_URL}/metrics/?page=${page}&per_page=7&t=${Date.now()}`;

        // Add filter params if set
        if (props.developerId) {
            url += `&developer_id=${props.developerId}`;
        }
        if (props.dateFrom) {
            url += `&date_from=${props.dateFrom}`;
        }
        if (props.dateTo) {
            url += `&date_to=${props.dateTo}`;
        }
        if (props.scoreMin !== undefined && props.scoreMin !== null && props.scoreMin !== '') {
            url += `&score_min=${props.scoreMin}`;
        }
        if (props.scoreMax !== undefined && props.scoreMax !== null && props.scoreMax !== '') {
            url += `&score_max=${props.scoreMax}`;
        }

        const response = await fetch(url, {
            headers: {
                'Cache-Control': 'no-cache',
                'Accept': 'application/json'
            }
        });
        if (!response.ok) throw new Error(await response.text());
        const result = await response.json();
        archiveData.value = result.data || [];
        pagination.value = result.pagination || { page: 1, per_page: 7, total_days: 0, total_pages: 1 };
    } catch (err) {
        error.value = `Failed to load history: ${err}`;
    } finally {
        loading.value = false;
    }
};

const goToPage = (page: number) => {
    if (page >= 1 && page <= pagination.value.total_pages) {
        fetchHistory(page);
    }
};

const openDetail = (item: DailyMetric, date: string) => {
    if (!item.developer_id) return;
    selectedDeveloperId.value = item.developer_id;
    selectedDeveloperName.value = item.developer;
    selectedDate.value = date;
    detailVisible.value = true;
};

const formatDate = (dateStr: string) => {
    if (!dateStr) return '';
    const [year, month, day] = dateStr.split('-').map(Number);
    const date = new Date(year, month - 1, day);
    return date.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'numeric', day: 'numeric' });
};

const getQualityGrade = (churnScore: number | undefined): string => {
    if (churnScore === undefined || churnScore === null) return 'N/A';
    if (churnScore <= 0.2) return 'A';
    if (churnScore <= 0.4) return 'B';
    if (churnScore <= 0.6) return 'C';
    if (churnScore <= 0.8) return 'D';
    return 'F';
};

// Timezone and filter props
const props = defineProps<{
    timezone?: string;
    developerId?: number | null;
    dateFrom?: string;
    dateTo?: string;
    scoreMin?: number | string;
    scoreMax?: number | string;
}>();

const currentTimezone = computed(() => props.timezone || 'Asia/Tehran');

const formatTimeInZone = (timeStr: string | null) => {
    if (!timeStr) return '-';

    // Try to parse ISO string directly
    const date = new Date(timeStr);
    if (isNaN(date.getTime())) return timeStr;

    try {
        return new Intl.DateTimeFormat('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
            timeZone: currentTimezone.value
        }).format(date);
    } catch (e) {
        console.error('Timezone error', e);
        return timeStr;
    }
};

// Watch for filter changes and refetch
watch(
    () => [props.developerId, props.dateFrom, props.dateTo, props.scoreMin, props.scoreMax],
    () => {
        fetchHistory(1);
    }
);

onMounted(() => {
    fetchHistory(1);
});
</script>

<template>
    <Card class="mt-8">
        <CardHeader>
            <CardTitle class="flex justify-between items-center">
                <span>Activity Archive</span>
                <span v-if="pagination.total_days > 0" class="text-sm font-normal text-muted-foreground">
          {{ pagination.total_days }} days total
        </span>
            </CardTitle>
            <CardDescription>
                Click on any row to see detailed breakdown
            </CardDescription>
        </CardHeader>
        <CardContent>
            <div v-if="loading" class="text-center p-4">Loading history...</div>
            <div v-if="error" class="p-4 mb-4 text-red-700 bg-red-100 rounded">{{ error }}</div>

            <div v-if="!loading && archiveData.length === 0" class="text-center text-gray-500">
                No historical data found.
            </div>

            <div v-for="day in archiveData" :key="day.date" class="mb-6 border-b pb-4 last:border-0">
                <h3 class="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">{{ formatDate(day.date) }}</h3>

                <div class="rounded-md border">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Developer</TableHead>
                                <TableHead>Commits</TableHead>
                                <TableHead>Start</TableHead>
                                <TableHead>End</TableHead>
                                <TableHead>Duration</TableHead>
                                <TableHead>Score</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            <TableRow
                                v-for="item in day.items"
                                :key="item.developer"
                                class="cursor-pointer hover:bg-muted/50"
                                @click="openDetail(item, day.date)"
                            >
                                <TableCell class="font-medium">{{ item.developer }}</TableCell>
                                <TableCell>{{ item.commits }}</TableCell>
                                <TableCell>{{ formatTimeInZone(item.start ?? null) }}</TableCell>
                                <TableCell>{{ formatTimeInZone(item.end ?? null) }}</TableCell>
                                <TableCell>{{ item.coding_time }}</TableCell>
                                <TableCell>
                            <span class="font-bold" :class="item.score > 50 ? 'text-green-600' : item.score > 0 ? 'text-yellow-600' : 'text-gray-400'">
                                {{ item.score.toFixed(1) }}-{{ getQualityGrade(item.churn_score) }}
                            </span>
                                </TableCell>
                            </TableRow>
                            <!-- Total Row -->
                            <TableRow class="bg-muted font-bold hover:bg-muted">
                                <TableCell>Total</TableCell>
                                <TableCell>{{ day.items.reduce((sum, i) => sum + i.commits, 0) }}</TableCell>
                                <TableCell>-</TableCell>
                                <TableCell>-</TableCell>
                                <TableCell>
                                    {{ day.items.reduce((sum, i) => sum + (parseInt(i.coding_time) || 0), 0) }} mins
                                </TableCell>
                                <TableCell>
                                    {{ day.items.reduce((sum, i) => sum + i.score, 0).toFixed(1) }}
                                </TableCell>
                            </TableRow>
                        </TableBody>
                    </Table>
                </div>
            </div>

            <!-- Pagination Controls -->
            <div v-if="pagination.total_pages > 1" class="flex items-center justify-center gap-4 mt-6 pt-4 border-t">
                <Button
                    variant="outline"
                    size="sm"
                    :disabled="pagination.page <= 1"
                    @click="goToPage(pagination.page - 1)"
                >
                    <ChevronLeft class="h-4 w-4 mr-1" />
                    Previous
                </Button>

                <div class="flex items-center gap-2">
                    <span class="text-sm text-muted-foreground">Page</span>
                    <span class="font-medium">{{ pagination.page }}</span>
                    <span class="text-sm text-muted-foreground">of</span>
                    <span class="font-medium">{{ pagination.total_pages }}</span>
                </div>

                <Button
                    variant="outline"
                    size="sm"
                    :disabled="pagination.page >= pagination.total_pages"
                    @click="goToPage(pagination.page + 1)"
                >
                    Next
                    <ChevronRight class="h-4 w-4 ml-1" />
                </Button>
            </div>
        </CardContent>
    </Card>

    <!-- Detail Modal -->
    <DeveloperDayDetail
        v-model:visible="detailVisible"
        :developer-id="selectedDeveloperId"
        :developer-name="selectedDeveloperName"
        :date="selectedDate"
    />
</template>
