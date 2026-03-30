<template>
  <div class="rounded-xl border border-fuchsia-500/30 bg-slate-800/70 p-4">
    <h3 class="mb-3 text-lg font-medium text-fuchsia-200">Metrics</h3>

    <div v-if="rows.length" class="space-y-4">
      <div v-for="section in sectionedRows" :key="section.group" class="rounded-lg border border-fuchsia-500/20 bg-slate-900/60 p-3">
        <h4 class="mb-2 text-sm font-semibold uppercase tracking-wide text-fuchsia-300">{{ section.group }}</h4>
        <DataTable :value="section.items" size="small" responsiveLayout="scroll" class="metrics-table">
          <Column field="metric" header="Metric" />
          <Column field="value" header="Value" />
        </DataTable>
      </div>
    </div>

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

const sectionedRows = computed(() => {
  const groups = new Map()

  rows.value.forEach(({ name, value }) => {
    const [group, ...rest] = name.split('.')
    const metricName = rest.length ? rest.join(' · ') : group

    if (!groups.has(group)) groups.set(group, [])
    groups.get(group).push({ metric: metricName, value })
  })

  return Array.from(groups.entries()).map(([group, items]) => ({ group, items }))
})
</script>
