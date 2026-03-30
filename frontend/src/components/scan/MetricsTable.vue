<template>
  <div class="rounded-xl border border-fuchsia-500/30 bg-slate-800/70 p-4">
    <h3 class="mb-3 text-lg font-medium text-fuchsia-200">Metrics</h3>
    <DataTable v-if="rows.length" :value="rows" size="small" responsiveLayout="scroll">
      <Column field="name" header="Metric" />
      <Column field="value" header="Value" />
    </DataTable>
    <p v-else class="text-slate-300">No metrics available.</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'

const props = defineProps({
  metrics: {
    type: Object,
    default: () => ({})
  }
})

function flattenMetrics(input, prefix = '') {
  return Object.entries(input).flatMap(([key, value]) => {
    const name = prefix ? `${prefix}.${key}` : key

    if (value && typeof value === 'object' && !Array.isArray(value)) {
      return flattenMetrics(value, name)
    }

    if (Array.isArray(value)) {
      return [{ name, value: value.join(', ') }]
    }

    return [{ name, value: typeof value === 'number' ? value.toFixed(4) : String(value) }]
  })
}

const rows = computed(() => flattenMetrics(props.metrics))
</script>
