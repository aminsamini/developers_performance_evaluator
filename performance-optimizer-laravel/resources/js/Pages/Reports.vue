<script setup lang="ts">
import AppLayout from '@/Layouts/AppLayout.vue';
import { ref, onMounted, computed, watch } from 'vue';
import { router } from '@inertiajs/vue3';
// ... imports

import { API_BASE_URL } from '../config';
import ChartCard from '@/components/reports/ChartCard.vue';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Loader2, Filter, AlertCircle, ArrowLeft } from 'lucide-vue-next';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import DateRangePicker from '@/components/ui/date-range-picker/DateRangePicker.vue';
import MultiSelect from '@/components/ui/multi-select/MultiSelect.vue';
import { parseDate, type DateValue } from '@internationalized/date';

// Types
interface ReportData {
  time_series: any[];
  languages: any[];
  projects: any[];
  editors: any[];
  operating_systems: any[];
  dependencies: any[];
  categories: any[];
  developer_stats: any[];
  totals: any; // { total_seconds, total_hours, active_repos }
}

// State
const loading = ref(false);
const error = ref<string | null>(null);
const reportData = ref<ReportData | null>(null);
const developers = ref<any[]>([]);

// Filters
const dateFrom = ref(new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]); // Last 60 days
const dateTo = ref(new Date().toISOString().split('T')[0]);
const selectedDevIds = ref<number[]>([]);

// Shadcn Date Range Logic
const dateRange = ref<{ start: DateValue, end: DateValue } | undefined>({
    start: parseDate(dateFrom.value),
    end: parseDate(dateTo.value)
});

watch(dateRange, (val) => {
    if (val?.start) dateFrom.value = val.start.toString();
    if (val?.end) dateTo.value = val.end.toString();
});

// Fetch Helpers
const fetchDevelopers = async () => {
    try {
        const res = await fetch(`${API_BASE_URL}/developers/`);
        if (res.ok) developers.value = await res.json();
    } catch (e) { console.error(e); }
};

const generateReport = async () => {
    loading.value = true;
    error.value = null;
    try {
        const res = await fetch(`${API_BASE_URL}/reports/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                from_date: dateFrom.value,
                to_date: dateTo.value,
                developer_ids: selectedDevIds.value.length > 0 ? selectedDevIds.value : null
            })
        });
        if (!res.ok) throw new Error("Failed to generate report");
        reportData.value = await res.json();
    } catch (e: any) {
        error.value = e.message || "Unknown error";
    } finally {
        loading.value = false;
    }
};

// --- Chart Configurations ---

// 1. Daily Coding Activity (Line)
const dailyActivityChart = computed(() => {
    if (!reportData.value) return null;
    const labels = reportData.value.time_series.map(d => d.date);
    const data = reportData.value.time_series.map(d => (d.total_seconds / 3600).toFixed(2));

    return {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Coding Hours',
                data,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { y: { title: { display: true, text: 'Hours' } } }
        }
    };
});

// 4. Language Distribution (Pie)
const languageDistChart = computed(() => {
    if (!reportData.value) return null;
    const top10 = reportData.value.languages.slice(0, 10);

    return {
        type: 'doughnut',
        data: {
            labels: top10.map(l => l.name),
            datasets: [{
                data: top10.map(l => (l.total_seconds / 3600).toFixed(1)),
                backgroundColor: [
                    '#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ec4899',
                    '#ef4444', '#06b6d4', '#84cc16', '#6366f1', '#a855f7'
                ],
                borderWidth: 1
            }]
        },
        options: {
            plugins: { legend: { position: 'right' } }
        }
    };
});

// 10. Project Distribution (Pie)
const projectDistChart = computed(() => {
    if (!reportData.value) return null;
    const top10 = reportData.value.projects.slice(0, 10);

    return {
        type: 'pie',
        data: {
            labels: top10.map(p => p.name),
            datasets: [{
                data: top10.map(p => (p.total_seconds / 3600).toFixed(1)),
                backgroundColor: [
                    '#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ec4899',
                    '#ef4444', '#06b6d4', '#84cc16', '#6366f1', '#a855f7'
                ],
                borderWidth: 1
            }]
        },
        options: {
            plugins: { legend: { position: 'right' } }
        }
    };
});

// 16. Editor Usage (Bar)
const editorChart = computed(() => {
    if (!reportData.value) return null;
    const items = reportData.value.editors.slice(0, 5);

    return {
        type: 'bar',
        data: {
            labels: items.map(i => i.name),
            datasets: [{
                label: 'Hours',
                data: items.map(i => (i.total_seconds / 3600).toFixed(1)),
                backgroundColor: '#8b5cf6',
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            plugins: { legend: { display: false } }
        }
    };
});

// --- NEW CHARTS ---

// 2. Weekly Activity (Day of Week Heatmap Proxy)
// Data prep for both ChartCard and Modal
const weeklyData = computed(() => {
    if (!reportData.value) return [];

    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const totals = [0, 0, 0, 0, 0, 0, 0];

    reportData.value.time_series.forEach(d => {
        const date = new Date(d.date);
        const dayIdx = date.getDay(); // 0-6
        totals[dayIdx] += d.total_seconds;
    });

    return days.map((day, idx) => ({
        name: day,
        total_seconds: totals[idx]
    }));
});

const weeklyHeatmapChart = computed(() => {
    if (weeklyData.value.length === 0) return null;

    const data = weeklyData.value;
    // For heatmap coloring relative to max
    const maxVal = Math.max(...data.map(d => d.total_seconds)) || 1;

    return {
        type: 'bar',
        data: {
            labels: data.map(d => d.name),
            datasets: [{
                label: 'Total Hours',
                data: data.map(d => (d.total_seconds / 3600).toFixed(1)),
                backgroundColor: (ctx: any) => {
                    const val = ctx.raw || 0;
                    // Normalize 0.2 to 1.0 opacity based on value
                    const opacity = Math.max(0.2, Math.min(1, val / (maxVal / 3600)));
                    return `rgba(59, 130, 246, ${opacity})`;
                },
                borderRadius: 4
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { y: { title: { display: true, text: 'Total Hours' } } }
        }
    };
});

// 3. Cumulative Coding Hours (Area)
const cumulativeChart = computed(() => {
    if (!reportData.value) return null;

    let runningTotal = 0;
    const labels: string[] = [];
    const data: number[] = [];

    reportData.value.time_series.forEach(d => {
        runningTotal += d.total_seconds;
        labels.push(d.date);
        data.push(Number((runningTotal / 3600).toFixed(2)));
    });

    return {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Cumulative Hours',
                data,
                borderColor: '#10b981', // emerald-500
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { y: { title: { display: true, text: 'Total Hours' } } }
        }
    };
});

// 5. Language Time Comparison (Horizontal Bar)
// Similar to Distribution but Bar format as requested
const languageTimeChart = computed(() => {
    if (!reportData.value) return null;
    const top10 = reportData.value.languages.slice(0, 10);

    return {
        type: 'bar',
        data: {
            labels: top10.map(l => l.name),
            datasets: [{
                label: 'Hours',
                data: top10.map(l => (l.total_seconds / 3600).toFixed(1)),
                backgroundColor: [
                    '#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ec4899',
                    '#ef4444', '#06b6d4', '#84cc16', '#6366f1', '#a855f7'
                ],
                borderRadius: 4,
                barPercentage: 0.6
            }]
        },
        options: {
            indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: { x: { title: { display: true, text: 'Hours' } } }
        }
    };
});
// 6. Language Trend Over Time (Stacked Area)
const languageTrendChart = computed(() => {
    if (!reportData.value) return null;

    const labels = reportData.value.time_series.map(d => d.date);

    // Identify top languages to keep chart readable (e.g. Top 7 + Others)
    const topLangs = reportData.value.languages.slice(0, 7).map(l => l.name);

    // Palette
    const palette = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ec4899', '#ef4444', '#06b6d4'];

    const datasets = topLangs.map((lang, idx) => {
        return {
            label: lang,
            data: reportData.value!.time_series.map(day => {
                const dayLangs = day.languages || {};
                return ((dayLangs[lang] || 0) / 3600).toFixed(2);
            }),
            backgroundColor: palette[idx],
            borderColor: palette[idx],
            fill: true,
            tension: 0.4,
            pointRadius: 0
        };
    });

    return {
        type: 'line',
        data: { labels, datasets },
        options: {
            plugins: { legend: { display: true, position: 'top' } },
            scales: { y: { stacked: true, title: { display: true, text: 'Hours' } } }
        }
    };
});

// 7. Dependency Distribution (Pie)
const dependencyPieChart = computed(() => {
    if (!reportData.value || reportData.value.dependencies.length === 0) return null;
    const items = reportData.value.dependencies.slice(0, 10);

    return {
        type: 'pie',
        data: {
            labels: items.map(i => i.name),
            datasets: [{
                data: items.map(i => (i.total_seconds / 3600).toFixed(2)),
                backgroundColor: [
                    '#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ec4899',
                    '#ef4444', '#06b6d4', '#84cc16', '#6366f1', '#a855f7'
                ]
            }]
        },
        options: { plugins: { legend: { position: 'right' } } }
    };
});

// 8 & 9. Dependency Time & Top 10 (Merged into one robust Bar Chart)
const dependencyBarChart = computed(() => {
    if (!reportData.value || reportData.value.dependencies.length === 0) return null;
    const items = reportData.value.dependencies.slice(0, 15);

    return {
        type: 'bar',
        data: {
            labels: items.map(i => i.name),
            datasets: [{
                label: 'Hours',
                data: items.map(i => (i.total_seconds / 3600).toFixed(2)),
                backgroundColor: '#ec4899',
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            plugins: { legend: { display: false } }
        }
    };
});

// 11. Project Hours Comparison (Bar)
const projectHoursChart = computed(() => {
    if (!reportData.value) return null;
    const items = reportData.value.projects.slice(0, 15);

    return {
        type: 'bar',
        data: {
            labels: items.map(p => p.name),
            datasets: [{
                label: 'Hours',
                data: items.map(p => (p.total_seconds / 3600).toFixed(1)),
                backgroundColor: '#10b981',
                borderRadius: 4
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { y: { title: { display: true, text: 'Hours' } } }
        }
    };
});

// 12. Code Changes by Project (Grouped Bar)
const projectChangesChart = computed(() => {
    if (!reportData.value) return null;
    const items = reportData.value.projects.slice(0, 10);

    // REMOVED CHECK: Ensure chart renders even if 0 lines to verify UI presence
    // const hasData = items.some(p => (p.lines_added || 0) > 0 || (p.lines_deleted || 0) > 0);
    // if (!hasData) return null;

    return {
        type: 'bar',
        data: {
            labels: items.map(p => p.name),
            datasets: [
                {
                    label: 'Added',
                    data: items.map(p => p.lines_added || 0),
                    backgroundColor: '#10b981',
                    borderRadius: 2
                },
                {
                    label: 'Deleted',
                    data: items.map(p => -(p.lines_deleted || 0)),
                    backgroundColor: '#ef4444',
                    borderRadius: 2
                }
            ]
        },
        options: {
            plugins: { legend: { display: true } },
            scales: { x: { stacked: true }, y: { stacked: true, title: { display: true, text: 'Lines' } } }
        }
    };
});

// 13. Lines of Code Gauge (Doughnut Trick)
const linesGaugeChart = computed(() => {
    if (!reportData.value) return null;
    const totals = reportData.value.time_series.reduce((acc, curr) => {
        acc.added += curr.human_additions || 0;
        acc.deleted += curr.human_deletions || 0;
        return acc;
    }, { added: 0, deleted: 0 });

    const total_vol = totals.added + totals.deleted;
    const ratio = total_vol > 0 ? (totals.added / total_vol) * 100 : 50;

    return {
        type: 'doughnut',
        data: {
            labels: ['Net Positive', 'Churn/Deleted'],
            datasets: [{
                data: [ratio, 100 - ratio],
                backgroundColor: ['#10b981', '#ef4444'],
                circumference: 180,
                rotation: 270,
                borderRadius: 4
            }]
        },
        options: {
            aspectRatio: 2,
            plugins: {
                legend: { display: true },
                title: { display: true, text: `Net: ${totals.added - totals.deleted} Lines`, position: 'bottom' }
            }
        }
    };
});

// 14. Code Velocity Trend (Line)
const velocityTrendChart = computed(() => {
    if (!reportData.value) return null;

    const labels = reportData.value.time_series.map(d => d.date);
    const data = reportData.value.time_series.map(d => (d.human_additions || 0) + (d.human_deletions || 0));

    return {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Velocity (Lines Changed)',
                data,
                borderColor: '#8b5cf6',
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { y: { title: { display: true, text: 'Lines Changed' } } }
        }
    };
});

// 15. Efficiency Ratio (Scatter)
const efficiencyScatterChart = computed(() => {
    if (!reportData.value) return null;

    const dataset = reportData.value.time_series.map(d => ({
        x: Number((d.total_seconds / 3600).toFixed(2)),
        y: (d.human_additions || 0) + (d.human_deletions || 0),
        date: d.date
    }));

    return {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Daily Performance',
                data: dataset,
                backgroundColor: '#f59e0b'
            }]
        },
        options: {
            plugins: {
                title: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx: any) => `${ctx.raw.date}: ${ctx.raw.y} lines in ${ctx.raw.x} hrs`
                    }
                }
            },
            scales: {
                x: { title: { display: true, text: 'Hours Coded' } },
                y: { title: { display: true, text: 'Lines Changed' } }
            }
        }
    };
});

// 17. Category Breakdown (Pie)
const categoryPieChart = computed(() => {
    if (!reportData.value || !reportData.value.categories) return null;
    const items = reportData.value.categories.slice(0, 6);

    return {
        type: 'pie',
        data: {
            labels: items.map(c => c.name),
            datasets: [{
                data: items.map(c => (c.total_seconds / 3600).toFixed(2)),
                backgroundColor: [
                    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'
                ]
            }]
        },
        options: { plugins: { legend: { position: 'right' } } }
    };
});

// 18. Hour Efficiency Score (Trend Line)
const efficiencyTrendChart = computed(() => {
    if (!reportData.value) return null;

    const labels = reportData.value.time_series.map(d => d.date);
    const data = reportData.value.time_series.map(d => {
        const hrs = d.total_seconds / 3600;
        const lines = (d.human_additions || 0) + (d.human_deletions || 0);
        return hrs > 0 ? (lines / hrs).toFixed(1) : 0;
    });

    return {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Lines / Hour',
                data,
                borderColor: '#6366f1',
                pointRadius: 2,
                tension: 0.2
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { y: { title: { display: true, text: 'Lines/Hr' } } }
        }
    };
});

// 22. Commit Frequency Timeline (Line)
const commitTimelineChart = computed(() => {
    if (!reportData.value) return null;

    const labels = reportData.value.time_series.map(d => d.date);
    const data = reportData.value.time_series.map(d => d.commits);

    return {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Commits',
                data,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { y: { title: { display: true, text: 'Commits' } } }
        }
    };
});

// 24. Team Member Activity (Horizontal Bar)
const teamActivityChart = computed(() => {
    if (!reportData.value || !reportData.value.developer_stats) return null;
    const items = reportData.value.developer_stats;

    return {
        type: 'bar',
        data: {
            labels: items.map(d => d.name),
            datasets: [{
                label: 'Hours',
                data: items.map(d => (d.total_seconds / 3600).toFixed(1)),
                backgroundColor: '#3b82f6',
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: { x: { title: { display: true, text: 'Hours' } } }
        }
    };
});

// 26. Team Language Preferences (Grouped Bar - Top 3 per Dev)
const teamLanguageChart = computed(() => {
    if (!reportData.value || !reportData.value.developer_stats) return null;
    const items = reportData.value.developer_stats.slice(0, 5);

    const allLangs = new Set();
    items.forEach(d => d.top_languages.forEach(l => allLangs.add(l.name)));
    const langLabels = Array.from(allLangs);

    const datasets = langLabels.map((lang, idx) => {
        return {
            label: lang as string,
            data: items.map(d => {
                const found = d.top_languages.find(l => l.name === lang);
                return found ? (found.seconds / 3600).toFixed(1) : 0;
            }),
            backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'][idx % 6]
        };
    });

    return {
        type: 'bar',
        data: {
            labels: items.map(d => d.name),
            datasets
        },
        options: {
            plugins: { legend: { display: true } },
            scales: { x: { stacked: true }, y: { stacked: true, title: { display: true, text: 'Hours' } } }
        }
    };
});

// 30. Technology Stack Radar
const techRadarChart = computed(() => {
    if (!reportData.value || reportData.value.languages.length === 0) return null;
    const items = reportData.value.languages.slice(0, 6); // Top 6

    return {
        type: 'radar',
        data: {
            labels: items.map(l => l.name),
            datasets: [{
                label: 'Usage Profile',
                data: items.map(l => (l.total_seconds / 3600).toFixed(1)),
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                borderColor: '#3b82f6',
                pointBackgroundColor: '#3b82f6'
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: {
                r: {
                    angleLines: { display: true },
                    suggestedMin: 0
                }
            }
        }
    };
});

const bestDayComputed = computed(() => {
    if (!reportData.value || !reportData.value.time_series) return null;
    const best = reportData.value.time_series.reduce((prev, current) => {
        return (prev.total_seconds > current.total_seconds) ? prev : current;
    }, { total_seconds: 0, date: '-' });
    return { date: best.date, hours: (best.total_seconds / 3600).toFixed(1) };
});

// 36. Goal Progress (Monthly Goal)
const goalProgressChart = computed(() => {
    if (!reportData.value) return null;
    const activeDevs = reportData.value.totals.active_developers || 1;
    const days = reportData.value.time_series.length || 1;
    const targetHours = days * 4 * activeDevs;
    const actualHours = reportData.value.totals.total_hours;
    const percentage = Math.min(100, (actualHours / targetHours) * 100);

    return {
        type: 'bar',
        data: {
            labels: ['Goal Achievement'],
            datasets: [
                {
                    label: 'Actual',
                    data: [actualHours],
                    backgroundColor: percentage >= 100 ? '#10b981' : '#3b82f6',
                    barThickness: 40
                },
                {
                    label: 'Target Gap',
                    data: [Math.max(0, targetHours - actualHours)],
                    backgroundColor: '#e5e7eb',
                    barThickness: 40
                }
            ]
        },
        options: {
            indexAxis: 'y',
            plugins: {
                tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ${c.raw} hrs` } },
                title: { display: true, text: `Target: ${targetHours} Hrs (${percentage.toFixed(0)}%)` }
            },
            scales: { x: { stacked: true, display: false }, y: { stacked: true, display: false } }
        }
    };
});

// 37. Productivity Forecast (Linear Regression)
const forecastChart = computed(() => {
    if (!reportData.value || reportData.value.time_series.length < 3) return null;

    const actualData = reportData.value.time_series.map((d, i) => ({ x: i, y: d.total_seconds / 3600, date: d.date }));

    // Simple Linear Regression (Least Squares)
    const n = actualData.length;
    let sumX = 0, sumY = 0, sumXY = 0, sumXX = 0;
    actualData.forEach(p => {
        sumX += p.x;
        sumY += p.y;
        sumXY += p.x * p.y;
        sumXX += p.x * p.x;
    });

    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    // Generate Forecast (Next 7 days)
    const forecastData = [];
    const lastDate = new Date(actualData[actualData.length - 1].date);

    for (let i = 0; i < n + 7; i++) {
        const val = slope * i + intercept;
        // Date label
        const d = new Date(actualData[0].date);
        d.setDate(d.getDate() + i);
        forecastData.push({ x: d.toISOString().split('T')[0], y: Math.max(0, val) });
    }

    return {
        type: 'line',
        data: {
            labels: forecastData.map(d => d.x),
            datasets: [
                {
                    label: 'Actual Hours',
                    data: actualData.map(d => Object.assign({}, {x: d.date, y: d.y})),
                    borderColor: '#3b82f6',
                    tension: 0.3
                },
                {
                    label: 'Trend / Forecast',
                    data: forecastData.map(d => d.y),
                    borderColor: '#f59e0b',
                    borderDash: [5, 5],
                    pointRadius: 0,
                    tension: 0
                }
            ]
        },
        options: {
            plugins: { title: { display: true, text: '7-Day Productivity Forecast' } },
            scales: { y: { title: { display: true, text: 'Hours' } } }
        }
    };
});
 import ChartDetailModal from '@/components/reports/ChartDetailModal.vue';
const detailModalOpen = ref(false);
const detailConfig = ref<{ title: string; chartType: string; rawData: any; computedData?: any; category: 'time'|'language'|'project'|'editor' } | null>(null);

const openDetail = (title: string, type: string, rawData: any[], category: 'time'|'language'|'project'|'editor', computedData: any = null) => {
    detailConfig.value = { title, chartType: type, rawData, computedData, category };
    detailModalOpen.value = true;
};

onMounted(() => {
    fetchDevelopers();
    generateReport();
});


</script>

<template>
  <AppLayout title="Reports">
  <div class="p-6 md:p-8 space-y-6 max-w-[1600px] mx-auto">

    <!-- Header & Filters -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="flex items-center gap-4">
            <Button variant="ghost" size="icon" @click="router.get(route('dashboard'))">
                <ArrowLeft class="h-6 w-6" />
            </Button>
            <div>
                <h1 class="text-3xl font-bold tracking-tight">Analytics Reports</h1>
                <p class="text-muted-foreground">Comprehensive deep-dive into productivity metrics.</p>
            </div>
        </div>

        <div class="flex flex-col md:flex-row md:items-center gap-4 bg-muted/40 p-2 rounded-lg">
             <DateRangePicker v-model="dateRange" class="w-auto" />

             <MultiSelect
                :options="developers.map(d => ({ label: d.name, value: d.id }))"
                v-model="selectedDevIds"
                placeholder="Select Developers"
                class="w-[250px]"
             />

            <Button @click="generateReport" :disabled="loading">
                <Loader2 v-if="loading" class="mr-2 h-4 w-4 animate-spin" />
                <Filter v-else class="mr-2 h-4 w-4" />
                Generate
            </Button>
        </div>
    </div>

    <Alert v-if="error" variant="destructive">
        <AlertCircle class="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{{ error }}</AlertDescription>
    </Alert>

    <!-- KPI Totals -->
    <div v-if="reportData" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
            <CardHeader class="pb-2"><CardTitle class="text-sm font-medium text-muted-foreground">Total Period Hours</CardTitle></CardHeader>
            <CardContent><div class="text-2xl font-bold">{{ reportData.totals.total_hours }} hrs</div></CardContent>
        </Card>
        <Card>
            <CardHeader class="pb-2"><CardTitle class="text-sm font-medium text-muted-foreground">Languages Used</CardTitle></CardHeader>
            <CardContent><div class="text-2xl font-bold">{{ reportData.languages.length }}</div></CardContent>
        </Card>
        <Card>
            <CardHeader class="pb-2"><CardTitle class="text-sm font-medium text-muted-foreground">Most Productive</CardTitle></CardHeader>
            <CardContent>
                <div class="text-2xl font-bold">{{ bestDayComputed?.date || '-' }}</div>
                <p class="text-xs text-muted-foreground">{{ bestDayComputed?.hours || 0 }} Hrs</p>
            </CardContent>
        </Card>
        <Card>
            <CardHeader class="pb-2"><CardTitle class="text-sm font-medium text-muted-foreground">Main Language</CardTitle></CardHeader>
            <CardContent>
                <div class="text-2xl font-bold">{{ reportData.languages[0]?.name || '-' }}</div>
                <p class="text-xs text-muted-foreground">{{ reportData.languages[0]?.percent || 0 }}%</p>
            </CardContent>
        </Card>
        <Card>
            <CardHeader class="pb-2"><CardTitle class="text-sm font-medium text-muted-foreground">Daily Average</CardTitle></CardHeader>
            <CardContent>
                <div class="text-2xl font-bold">{{ (reportData.totals.total_hours / (reportData.time_series.length || 1)).toFixed(1) }}h</div>
            </CardContent>
        </Card>
        <Card>
            <CardHeader class="pb-2"><CardTitle class="text-sm font-medium text-muted-foreground">Active Repositories</CardTitle></CardHeader>
            <CardContent><div class="text-2xl font-bold">{{ reportData.totals.active_repos || reportData.projects.length }}</div></CardContent>
        </Card>
        <Card>
             <CardHeader class="pb-2"><CardTitle class="text-sm font-medium text-muted-foreground">Editors Used</CardTitle></CardHeader>
            <CardContent><div class="text-2xl font-bold">{{ reportData.editors.length }}</div></CardContent>
        </Card>
    </div>

    <!-- Charts Grid -->
    <div v-if="reportData" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">

        <!-- Phase 7: Predictive Charts -->
        <ChartCard
            v-if="goalProgressChart"
            title="36. Goal Progress"
            :chartType="goalProgressChart.type"
            :chartData="goalProgressChart.data"
            :chartOptions="goalProgressChart.options"
            @expand="openDetail('Goal Progress', 'bar', [], 'time', goalProgressChart.data)"
        />

        <ChartCard
            v-if="forecastChart"
            title="37. Productivity Forecast"
            :chartType="forecastChart.type"
            :chartData="forecastChart.data"
            :chartOptions="forecastChart.options"
            @expand="openDetail('Productivity Forecast', 'line', reportData.time_series, 'time', forecastChart.data)"
        />
        <ChartCard
            v-if="dailyActivityChart"
            title="1. Daily Coding Activity Trend"
            :chartType="dailyActivityChart.type"
            :chartData="dailyActivityChart.data"
            :chartOptions="dailyActivityChart.options"
            @expand="openDetail('Daily Coding Activity Trend', 'line', reportData.time_series, 'time', dailyActivityChart.data)"
        />

        <ChartCard
            v-if="weeklyHeatmapChart"
            title="2. Weekly Activity (Day of Week)"
            :chartType="weeklyHeatmapChart.type"
            :chartData="weeklyHeatmapChart.data"
            :chartOptions="weeklyHeatmapChart.options"
            @expand="openDetail('Weekly Activity', 'bar', weeklyData, 'time')"
        />

        <ChartCard
            v-if="cumulativeChart"
            title="3. Cumulative Coding Hours"
            :chartType="cumulativeChart.type"
            :chartData="cumulativeChart.data"
            :chartOptions="cumulativeChart.options"
            @expand="openDetail('Cumulative Hours', 'line', reportData.time_series, 'time', cumulativeChart.data)"
        />

        <ChartCard
            v-if="languageDistChart"
            title="4. Language Distribution"
            :chartType="languageDistChart.type"
            :chartData="languageDistChart.data"
            :chartOptions="languageDistChart.options"
            @expand="openDetail('Language Distribution', 'doughnut', reportData.languages, 'language')"
        />
        <ChartCard
            v-if="projectDistChart"
            title="10. Project Distribution"
            :chartType="projectDistChart.type"
            :chartData="projectDistChart.data"
            :chartOptions="projectDistChart.options"
            @expand="openDetail('Project Distribution', 'pie', reportData.projects, 'project')"
        />

        <ChartCard
            v-if="languageTimeChart"
            title="5. Time Spent by Language"
            :chartType="languageTimeChart.type"
            :chartData="languageTimeChart.data"
            :chartOptions="languageTimeChart.options"
            @expand="openDetail('Time Spent by Language', 'bar', reportData.languages, 'language')"
        />

        <ChartCard
            v-if="languageTrendChart"
            title="6. Language Usage Evolution"
            :chartType="languageTrendChart.type"
            :chartData="languageTrendChart.data"
            :chartOptions="languageTrendChart.options"
            @expand="openDetail('Language Usage Evolution', 'line', reportData.time_series, 'time', languageTrendChart.data)"
        />

        <ChartCard
            v-if="dependencyPieChart"
            title="7. Dependency Distribution"
            :chartType="dependencyPieChart.type"
            :chartData="dependencyPieChart.data"
            :chartOptions="dependencyPieChart.options"
            @expand="openDetail('Dependency Distribution', 'pie', reportData.dependencies, 'language')"
        />

        <ChartCard
            v-if="dependencyBarChart"
            title="8. Top Dependencies (Hours)"
            :chartType="dependencyBarChart.type"
            :chartData="dependencyBarChart.data"
            :chartOptions="dependencyBarChart.options"
            @expand="openDetail('Top Dependencies', 'bar', reportData.dependencies, 'language')"
        />

        <ChartCard
            v-if="projectHoursChart"
            title="11. Project Hours Comparison"
            :chartType="projectHoursChart.type"
            :chartData="projectHoursChart.data"
            :chartOptions="projectHoursChart.options"
            @expand="openDetail('Project Hours', 'bar', reportData.projects, 'project')"
        />

        <ChartCard
            v-if="projectChangesChart"
            title="12. Code Changes by Project"
            :chartType="projectChangesChart.type"
            :chartData="projectChangesChart.data"
            :chartOptions="projectChangesChart.options"
            @expand="openDetail('Code Changes by Project', 'bar', reportData.projects, 'project')"
        />

        <ChartCard
            v-if="linesGaugeChart"
            title="13. Net Lines (Gauge)"
            :chartType="linesGaugeChart.type"
            :chartData="linesGaugeChart.data"
            :chartOptions="linesGaugeChart.options"
            @expand="openDetail('Net Lines', 'doughnut', [], 'time', linesGaugeChart.data)"
        />

        <ChartCard
            v-if="velocityTrendChart"
            title="14. Code Velocity Trend"
            :chartType="velocityTrendChart.type"
            :chartData="velocityTrendChart.data"
            :chartOptions="velocityTrendChart.options"
            @expand="openDetail('Velocity Trend', 'line', reportData.time_series, 'time', velocityTrendChart.data)"
        />

        <ChartCard
            v-if="efficiencyScatterChart"
            title="15. Efficiency Ratio (Lines/Hour)"
            :chartType="efficiencyScatterChart.type"
            :chartData="efficiencyScatterChart.data"
            :chartOptions="efficiencyScatterChart.options"
            @expand="openDetail('Efficiency Ratio', 'scatter', [], 'time', efficiencyScatterChart.data)"
        />

        <ChartCard
            v-if="editorChart"
            title="16. Editor Usage"
            :chartType="editorChart.type"
            :chartData="editorChart.data"
            :chartOptions="editorChart.options"
            @expand="openDetail('Editor Usage', 'bar', reportData.editors, 'editor')"
        />

        <ChartCard
            v-if="categoryPieChart"
            title="17. Activity Category Distribution"
            :chartType="categoryPieChart.type"
            :chartData="categoryPieChart.data"
            :chartOptions="categoryPieChart.options"
            @expand="openDetail('Category Breakdown', 'pie', reportData.categories, 'time')"
        />

        <ChartCard
            v-if="efficiencyTrendChart"
            title="18. Hourly Efficiency Trend"
            :chartType="efficiencyTrendChart.type"
            :chartData="efficiencyTrendChart.data"
            :chartOptions="efficiencyTrendChart.options"
            @expand="openDetail('Efficiency Trend', 'line', reportData.time_series, 'time', efficiencyTrendChart.data)"
        />

        <ChartCard
            v-if="commitTimelineChart"
            title="22. Commit Activity Timeline"
            :chartType="commitTimelineChart.type"
            :chartData="commitTimelineChart.data"
            :chartOptions="commitTimelineChart.options"
            @expand="openDetail('Commit Activity', 'line', reportData.time_series, 'time', commitTimelineChart.data)"
        />

        <ChartCard
            v-if="teamActivityChart"
            title="24. Team Member Activity"
            :chartType="teamActivityChart.type"
            :chartData="teamActivityChart.data"
            :chartOptions="teamActivityChart.options"
            @expand="openDetail('Team Activity', 'bar', reportData.developer_stats, 'project')"
        />

        <ChartCard
            v-if="teamLanguageChart"
            title="26. Team Technology Matrix (Top 5 Devs)"
            :chartType="teamLanguageChart.type"
            :chartData="teamLanguageChart.data"
            :chartOptions="teamLanguageChart.options"
            @expand="openDetail('Team Languages', 'bar', [], 'project', teamLanguageChart.data)"
        />

        <ChartCard
            v-if="techRadarChart"
            title="30. Technical Proficiency Radar"
            :chartType="techRadarChart.type"
            :chartData="techRadarChart.data"
            :chartOptions="techRadarChart.options"
            @expand="openDetail('Tech Radar', 'radar', reportData.languages, 'language', techRadarChart.data)"
        />
    </div>
  </div>

    <!-- Details Modal -->
    <ChartDetailModal
        v-if="detailConfig"
        :isOpen="detailModalOpen"
        @update:isOpen="detailModalOpen = $event"
        :title="detailConfig.title"
        :chartType="detailConfig.chartType"
        :rawData="detailConfig.rawData"
        :computedData="detailConfig.computedData"
        :category="detailConfig.category"
    />

    <!-- Empty State -->
    <div v-else-if="!loading && !reportData" class="text-center py-20 text-muted-foreground">
        Click "Generate" to view reports.
    </div>
  </AppLayout>
</template>
