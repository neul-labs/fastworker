<template>
  <div class="bg-white rounded-lg shadow-md">
    <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-gray-900">Workers</h2>
      <span class="text-sm text-gray-500">{{ workers.length }} total</span>
    </div>
    <div class="p-6">
      <div v-if="workers.length === 0" class="text-center py-8 text-gray-500">
        <svg class="h-12 w-12 mx-auto text-gray-400 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <p>No workers available</p>
      </div>
      <div v-else class="space-y-4">
        <div
          v-for="worker in workers"
          :key="worker.id"
          class="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
          :class="{ 'ring-2 ring-indigo-200': worker.is_control_plane }"
        >
          <div class="flex items-center space-x-3">
            <span
              :class="worker.status === 'active' ? 'bg-green-400' : 'bg-red-400'"
              class="h-3 w-3 rounded-full"
            ></span>
            <div>
              <div class="flex items-center space-x-2">
                <p class="font-medium text-gray-900">{{ worker.id }}</p>
                <span
                  v-if="worker.is_control_plane"
                  class="px-2 py-0.5 text-xs font-medium bg-indigo-100 text-indigo-700 rounded-full"
                >
                  Control Plane
                </span>
                <span
                  v-else
                  class="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 rounded-full"
                >
                  Subworker
                </span>
              </div>
              <p class="text-sm text-gray-500">{{ worker.address }}</p>
            </div>
          </div>
          <div class="text-right">
            <p class="text-sm font-medium text-gray-900">Load: {{ worker.load }}</p>
            <p class="text-xs text-gray-500">Last seen: {{ formatTime(worker.last_seen) }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'WorkersPanel',
  props: {
    workers: {
      type: Array,
      default: () => []
    }
  },
  setup() {
    const formatTime = (isoString) => {
      if (!isoString) return 'Never'
      try {
        const date = new Date(isoString)
        return date.toLocaleTimeString()
      } catch {
        return isoString
      }
    }

    return {
      formatTime
    }
  }
}
</script>
