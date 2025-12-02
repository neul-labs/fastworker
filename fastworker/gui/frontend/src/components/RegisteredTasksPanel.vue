<template>
  <div class="bg-white rounded-lg shadow-md">
    <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-gray-900">Registered Tasks</h2>
      <span class="text-sm text-gray-500">{{ tasks.length }} tasks</span>
    </div>
    <div class="p-6">
      <div v-if="tasks.length === 0" class="text-center py-8 text-gray-500">
        <svg class="h-12 w-12 mx-auto text-gray-400 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        <p>No tasks registered</p>
        <p class="text-sm mt-1">Load task modules with --task-modules</p>
      </div>
      <div v-else class="space-y-3">
        <div
          v-for="task in tasks"
          :key="task.name"
          class="p-3 bg-gray-50 rounded-lg"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <svg class="h-4 w-4 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span class="font-medium text-gray-900">{{ task.name }}</span>
            </div>
            <span class="text-xs text-gray-400 font-mono">{{ task.module }}</span>
          </div>
          <p v-if="task.doc" class="mt-1 text-sm text-gray-600 pl-6">{{ task.doc }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RegisteredTasksPanel',
  props: {
    tasks: {
      type: Array,
      default: () => []
    }
  }
}
</script>
