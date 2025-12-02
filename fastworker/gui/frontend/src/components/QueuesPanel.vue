<template>
  <div class="bg-white rounded-lg shadow-md">
    <div class="px-6 py-4 border-b border-gray-200">
      <h2 class="text-lg font-semibold text-gray-900">Task Queues</h2>
    </div>
    <div class="p-6">
      <div class="space-y-4">
        <div
          v-for="(queue, priority) in orderedQueues"
          :key="priority"
          class="flex items-center justify-between"
        >
          <div class="flex items-center space-x-3">
            <span
              :class="getPriorityColor(priority)"
              class="w-3 h-3 rounded-full"
            ></span>
            <span class="font-medium text-gray-700 capitalize">{{ priority }}</span>
          </div>
          <div class="flex items-center space-x-4">
            <div class="w-32 bg-gray-200 rounded-full h-2">
              <div
                :class="getPriorityBgColor(priority)"
                class="h-2 rounded-full transition-all duration-300"
                :style="{ width: `${getBarWidth(queue.count)}%` }"
              ></div>
            </div>
            <span class="text-sm font-medium text-gray-600 w-12 text-right">
              {{ queue.count }}
            </span>
          </div>
        </div>
      </div>

      <!-- Queue Preview -->
      <div v-if="hasQueuedTasks" class="mt-6 pt-4 border-t border-gray-200">
        <h3 class="text-sm font-medium text-gray-700 mb-3">Next Tasks</h3>
        <div class="space-y-2">
          <div
            v-for="task in previewTasks"
            :key="task.id"
            class="flex items-center justify-between text-sm bg-gray-50 px-3 py-2 rounded"
          >
            <span class="font-mono text-gray-600 truncate">{{ task.name }}</span>
            <span class="text-xs text-gray-400 ml-2">{{ task.id.slice(0, 8) }}...</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'QueuesPanel',
  props: {
    queues: {
      type: Object,
      default: () => ({})
    }
  },
  setup(props) {
    const priorityOrder = ['critical', 'high', 'normal', 'low']

    const orderedQueues = computed(() => {
      const result = {}
      for (const priority of priorityOrder) {
        result[priority] = props.queues[priority] || { count: 0, tasks: [] }
      }
      return result
    })

    const hasQueuedTasks = computed(() => {
      return Object.values(props.queues).some(q => q.count > 0)
    })

    const previewTasks = computed(() => {
      const tasks = []
      for (const priority of priorityOrder) {
        const queue = props.queues[priority]
        if (queue && queue.tasks) {
          tasks.push(...queue.tasks.slice(0, 3))
        }
        if (tasks.length >= 5) break
      }
      return tasks.slice(0, 5)
    })

    const getPriorityColor = (priority) => {
      const colors = {
        critical: 'bg-red-500',
        high: 'bg-orange-500',
        normal: 'bg-blue-500',
        low: 'bg-gray-400'
      }
      return colors[priority] || 'bg-gray-400'
    }

    const getPriorityBgColor = (priority) => {
      const colors = {
        critical: 'bg-red-500',
        high: 'bg-orange-500',
        normal: 'bg-blue-500',
        low: 'bg-gray-400'
      }
      return colors[priority] || 'bg-gray-400'
    }

    const getBarWidth = (count) => {
      if (count === 0) return 0
      // Logarithmic scale for better visualization
      const maxDisplay = 100
      const percentage = Math.min((Math.log10(count + 1) / Math.log10(maxDisplay + 1)) * 100, 100)
      return Math.max(percentage, 5) // Minimum 5% for visibility
    }

    return {
      orderedQueues,
      hasQueuedTasks,
      previewTasks,
      getPriorityColor,
      getPriorityBgColor,
      getBarWidth
    }
  }
}
</script>
