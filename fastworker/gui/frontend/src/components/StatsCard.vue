<template>
  <div class="bg-white rounded-lg shadow-md p-6">
    <div class="flex items-center">
      <div :class="iconBgClass" class="p-3 rounded-full">
        <div :class="iconColorClass">
          <slot name="icon"></slot>
        </div>
      </div>
      <div class="ml-4">
        <p class="text-sm font-medium text-gray-500">{{ title }}</p>
        <p class="text-2xl font-semibold text-gray-900">{{ value }}</p>
        <p v-if="subtitle" class="text-xs text-gray-400 mt-1">{{ subtitle }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'StatsCard',
  props: {
    title: {
      type: String,
      required: true
    },
    value: {
      type: [String, Number],
      required: true
    },
    subtitle: {
      type: String,
      default: ''
    },
    color: {
      type: String,
      default: 'blue',
      validator: (value) => ['green', 'yellow', 'blue', 'purple', 'red'].includes(value)
    }
  },
  setup(props) {
    const colorClasses = {
      green: { bg: 'bg-green-100', text: 'text-green-600' },
      yellow: { bg: 'bg-yellow-100', text: 'text-yellow-600' },
      blue: { bg: 'bg-blue-100', text: 'text-blue-600' },
      purple: { bg: 'bg-purple-100', text: 'text-purple-600' },
      red: { bg: 'bg-red-100', text: 'text-red-600' }
    }

    const iconBgClass = computed(() => colorClasses[props.color].bg)
    const iconColorClass = computed(() => colorClasses[props.color].text)

    return {
      iconBgClass,
      iconColorClass
    }
  }
}
</script>
