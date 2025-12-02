<template>
  <div class="bg-white rounded-lg shadow-md">
    <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-gray-900">Task Results</h2>
      <span class="text-sm text-gray-500">{{ total }} total in cache</span>
    </div>
    <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Task ID</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Result</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Completed</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cached</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-if="tasks.length === 0">
            <td colspan="5" class="px-6 py-12 text-center text-gray-500">
              <svg class="h-12 w-12 mx-auto text-gray-400 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <p>No task results in cache</p>
            </td>
          </tr>
          <tr v-for="task in tasks" :key="task.task_id" class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap">
              <span class="font-mono text-sm text-gray-900">{{ task.task_id.slice(0, 8) }}...</span>
              <button
                @click="copyTaskId(task.task_id)"
                class="ml-2 text-gray-400 hover:text-gray-600"
                title="Copy full ID"
              >
                <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span
                :class="getStatusClass(task.status)"
                class="px-2 py-1 text-xs font-medium rounded-full"
              >
                {{ task.status }}
              </span>
            </td>
            <td class="px-6 py-4">
              <div v-if="task.error" class="text-red-600 text-sm truncate max-w-xs" :title="task.error">
                {{ task.error }}
              </div>
              <div v-else-if="task.result" class="text-gray-900 text-sm truncate max-w-xs" :title="task.result">
                {{ task.result }}
              </div>
              <span v-else class="text-gray-400 text-sm">-</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ formatDateTime(task.completed_at) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ formatDateTime(task.cached_at) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="total > 0" class="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
      <div class="text-sm text-gray-700">
        Showing <span class="font-medium">{{ startItem }}</span> to <span class="font-medium">{{ endItem }}</span> of <span class="font-medium">{{ total }}</span> results
      </div>
      <div class="flex items-center space-x-2">
        <button
          @click="$emit('page-change', currentPage - 1)"
          :disabled="currentPage === 1 || loading"
          class="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        <div class="flex items-center space-x-1">
          <button
            v-for="page in visiblePages"
            :key="page"
            @click="$emit('page-change', page)"
            :disabled="loading"
            :class="[
              'px-3 py-1 border rounded-md text-sm font-medium',
              page === currentPage
                ? 'border-indigo-500 bg-indigo-50 text-indigo-600'
                : 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50'
            ]"
          >
            {{ page }}
          </button>
        </div>
        <button
          @click="$emit('page-change', currentPage + 1)"
          :disabled="currentPage === totalPages || loading"
          class="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'TasksTable',
  props: {
    tasks: {
      type: Array,
      default: () => []
    },
    total: {
      type: Number,
      default: 0
    },
    currentPage: {
      type: Number,
      default: 1
    },
    pageSize: {
      type: Number,
      default: 20
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['page-change'],
  setup(props) {
    const totalPages = computed(() => Math.ceil(props.total / props.pageSize))

    const startItem = computed(() => {
      if (props.total === 0) return 0
      return (props.currentPage - 1) * props.pageSize + 1
    })

    const endItem = computed(() => {
      return Math.min(props.currentPage * props.pageSize, props.total)
    })

    const visiblePages = computed(() => {
      const pages = []
      const total = totalPages.value
      const current = props.currentPage

      if (total <= 7) {
        for (let i = 1; i <= total; i++) pages.push(i)
      } else {
        if (current <= 4) {
          for (let i = 1; i <= 5; i++) pages.push(i)
          pages.push(total)
        } else if (current >= total - 3) {
          pages.push(1)
          for (let i = total - 4; i <= total; i++) pages.push(i)
        } else {
          pages.push(1)
          for (let i = current - 1; i <= current + 1; i++) pages.push(i)
          pages.push(total)
        }
      }
      return pages
    })

    const getStatusClass = (status) => {
      const classes = {
        success: 'bg-green-100 text-green-800',
        failure: 'bg-red-100 text-red-800',
        pending: 'bg-yellow-100 text-yellow-800',
        started: 'bg-blue-100 text-blue-800'
      }
      return classes[status] || 'bg-gray-100 text-gray-800'
    }

    const formatDateTime = (isoString) => {
      if (!isoString) return '-'
      try {
        const date = new Date(isoString)
        return date.toLocaleString()
      } catch {
        return isoString
      }
    }

    const copyTaskId = async (taskId) => {
      try {
        await navigator.clipboard.writeText(taskId)
      } catch (e) {
        console.error('Failed to copy:', e)
      }
    }

    return {
      totalPages,
      startItem,
      endItem,
      visiblePages,
      getStatusClass,
      formatDateTime,
      copyTaskId
    }
  }
}
</script>
