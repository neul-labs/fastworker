<template>
  <div class="min-h-screen">
    <!-- Header -->
    <header class="bg-indigo-600 text-white shadow-lg">
      <div class="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <svg class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <h1 class="text-2xl font-bold">FastWorker</h1>
          </div>
          <div class="flex items-center space-x-4">
            <span v-if="status" class="text-sm">
              <span class="inline-flex items-center">
                <span :class="status.running ? 'bg-green-400' : 'bg-red-400'" class="h-2 w-2 rounded-full mr-2"></span>
                {{ status.worker_id }}
              </span>
            </span>
            <button @click="refreshData" class="p-2 rounded-md hover:bg-indigo-500 transition-colors" title="Refresh">
              <svg class="h-5 w-5" :class="{ 'animate-spin': loading }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
      <!-- Error Alert -->
      <div v-if="error" class="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
        <span class="block sm:inline">{{ error }}</span>
        <button @click="error = null" class="absolute top-0 bottom-0 right-0 px-4 py-3">
          <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
          </svg>
        </button>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatsCard
          title="Workers"
          :value="workers.length"
          :subtitle="`${workers.filter(w => w.status === 'active').length} active`"
          color="green"
        >
          <template #icon>
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </template>
        </StatsCard>

        <StatsCard
          title="Queued Tasks"
          :value="status?.tasks?.queued ?? 0"
          subtitle="Waiting for processing"
          color="yellow"
        >
          <template #icon>
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </template>
        </StatsCard>

        <StatsCard
          title="Cached Results"
          :value="status?.tasks?.cached_results ?? 0"
          :subtitle="`Max: ${status?.cache?.max_size ?? 0}`"
          color="blue"
        >
          <template #icon>
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
            </svg>
          </template>
        </StatsCard>

        <StatsCard
          title="Registered Tasks"
          :value="registeredTasks.length"
          subtitle="Task definitions"
          color="purple"
        >
          <template #icon>
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
          </template>
        </StatsCard>
      </div>

      <!-- Three Column Layout -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <!-- Workers Panel -->
        <WorkersPanel :workers="workers" />

        <!-- Queue Status Panel -->
        <QueuesPanel :queues="queues" />

        <!-- Registered Tasks Panel -->
        <RegisteredTasksPanel :tasks="registeredTasks" />
      </div>

      <!-- Tasks Table -->
      <TasksTable
        :tasks="tasks"
        :total="tasksTotal"
        :current-page="currentPage"
        :page-size="pageSize"
        :loading="loading"
        @page-change="handlePageChange"
      />
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t mt-8">
      <div class="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between text-sm text-gray-500">
          <span>FastWorker Management GUI</span>
          <span v-if="lastUpdate">Last updated: {{ lastUpdate }}</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import StatsCard from './components/StatsCard.vue'
import WorkersPanel from './components/WorkersPanel.vue'
import QueuesPanel from './components/QueuesPanel.vue'
import TasksTable from './components/TasksTable.vue'
import RegisteredTasksPanel from './components/RegisteredTasksPanel.vue'

export default {
  name: 'App',
  components: {
    StatsCard,
    WorkersPanel,
    QueuesPanel,
    TasksTable,
    RegisteredTasksPanel
  },
  setup() {
    const status = ref(null)
    const workers = ref([])
    const queues = ref({})
    const tasks = ref([])
    const tasksTotal = ref(0)
    const registeredTasks = ref([])
    const cacheStats = ref(null)
    const loading = ref(false)
    const error = ref(null)
    const lastUpdate = ref(null)

    // Pagination state
    const currentPage = ref(1)
    const pageSize = ref(20)

    let refreshInterval = null

    const fetchData = async () => {
      loading.value = true
      error.value = null

      try {
        const offset = (currentPage.value - 1) * pageSize.value

        const [statusRes, workersRes, queuesRes, cacheRes, tasksRes, registeredRes] = await Promise.all([
          fetch('/api/status'),
          fetch('/api/workers'),
          fetch('/api/queues'),
          fetch('/api/cache'),
          fetch(`/api/tasks?limit=${pageSize.value}&offset=${offset}`),
          fetch('/api/registered-tasks')
        ])

        if (!statusRes.ok) throw new Error('Failed to fetch status')

        status.value = await statusRes.json()

        const workersData = await workersRes.json()
        workers.value = workersData.workers || []

        const queuesData = await queuesRes.json()
        queues.value = queuesData.queues || {}

        cacheStats.value = await cacheRes.json()

        const tasksData = await tasksRes.json()
        tasks.value = tasksData.tasks || []
        tasksTotal.value = tasksData.total || 0

        const registeredData = await registeredRes.json()
        registeredTasks.value = registeredData.tasks || []

        lastUpdate.value = new Date().toLocaleTimeString()
      } catch (e) {
        error.value = e.message || 'Failed to connect to control plane'
        console.error('Error fetching data:', e)
      } finally {
        loading.value = false
      }
    }

    const refreshData = () => {
      fetchData()
    }

    const handlePageChange = async (page) => {
      currentPage.value = page
      await fetchData()
    }

    onMounted(() => {
      fetchData()
      // Auto-refresh every 5 seconds
      refreshInterval = setInterval(fetchData, 5000)
    })

    onUnmounted(() => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
    })

    return {
      status,
      workers,
      queues,
      tasks,
      tasksTotal,
      registeredTasks,
      cacheStats,
      loading,
      error,
      lastUpdate,
      currentPage,
      pageSize,
      refreshData,
      handlePageChange
    }
  }
}
</script>
