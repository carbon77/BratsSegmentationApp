<template>
  <section class="space-y-4">
    <Card>
      <template #title>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <span class="text-indigo-200">Scan {{ caseId }}</span>
          <Button
            label="Delete scan"
            icon="pi pi-trash"
            severity="danger"
            outlined
            :loading="isDeleting"
            @click="removeScan"
          />
        </div>
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
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'

import MetricsTable from '../components/scan/MetricsTable.vue'
import SliceViewer from '../components/scan/SliceViewer.vue'
import { deleteScan, fetchMetrics } from '../services/api'

const props = defineProps({
  caseId: {
    type: String,
    required: true
  }
})

const router = useRouter()
const metrics = ref({})
const isLoading = ref(false)
const isDeleting = ref(false)
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

async function removeScan() {
  isDeleting.value = true
  errorMessage.value = ''

  try {
    await deleteScan(props.caseId)
    await router.push('/')
  } catch {
    errorMessage.value = 'Could not delete this scan.'
  } finally {
    isDeleting.value = false
  }
}

onMounted(loadMetrics)
</script>
