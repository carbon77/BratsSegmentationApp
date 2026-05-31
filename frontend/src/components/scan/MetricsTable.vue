<template>
  <Panel :header="t('metrics')">
    <Accordion v-if="rows.length" :activeIndex="0">
      <AccordionTab v-for="section in sectionedRows" :key="section.group" :header="section.group.toUpperCase()">
        <DataTable :value="section.items" size="small" responsiveLayout="scroll">
          <Column field="metric" :header="t('metric')" />
          <Column field="value" :header="t('value')" />
        </DataTable>
      </AccordionTab>
    </Accordion>

    <Message v-else severity="info">{{ t('noMetrics') }}</Message>
  </Panel>
</template>

<script setup>
import { computed } from 'vue'
import Accordion from 'primevue/accordion'
import AccordionTab from 'primevue/accordiontab'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Message from 'primevue/message'
import Panel from 'primevue/panel'

import { usePreferences } from '../../services/preferences'

const { t } = usePreferences()

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
