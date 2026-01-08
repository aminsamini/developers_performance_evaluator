import { ref, reactive } from 'vue';
import { API_BASE_URL } from '../config';

// Define types locally since they might not be exported from components
interface Developer {
    id: number;
    name: string;
}

// Global state
const developers = ref<Developer[]>([]);
const selectedTimezone = ref('Asia/Tehran');
// We can use a reactive object for summary stats or keep it specific to Dashboard if not needed globally.
// However, the "Sync Data" button in NavBar needs to show spinner based on summary loading or sync state.
const isSyncing = ref(false);

export function useGlobalState() {

    const fetchDevelopers = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/developers/`);
            if (response.ok) {
                developers.value = await response.json();
            }
        } catch (error) {
            console.error('Failed to fetch developers', error);
        }
    };

    return {
        developers,
        selectedTimezone,
        isSyncing,
        fetchDevelopers
    };
}
