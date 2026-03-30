<template>
  <section class="space-y-4">
    <Card>
      <template #title>
        <span class="text-indigo-200">Scan {{ caseId }}</span>
      </template>
      <template #content>
        <div v-if="isLoading" class="py-4">
          <ProgressSpinner style="width: 34px; height: 34px" strokeWidth="6" />
        </div>

        <div v-else class="space-y-4">
          <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>
          <MetricsTable :metrics="metrics" />
          <SliceViewer :case-id="caseId" :initial-slice="60" />
        </div>
      </template>
    </Card>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import Card from 'primevue/card'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'

import MetricsTable from '../components/scan/MetricsTable.vue'
import SliceViewer from '../components/scan/SliceViewer.vue'
import { fetchMetrics } from '../services/api'

const props = defineProps({
  caseId: {
    type: String,
    required: true
  }
})

const metrics = ref({})
const isLoading = ref(false)
const errorMessage = ref('')

async function loadMetrics() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const payload = await fetchMetrics(props.caseId)
    metrics.value = payload.metrics ?? {}
  } catch {
    errorMessage.value = 'Could not load scan metrics. It may still be processing.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadMetrics)
</script>
