<template>
  <section>
    <Panel>
      <template #header>
        <div class="scan-header">
          <Tag :value="`Scan ${caseId}`" severity="info" />
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

      <ProgressSpinner v-if="isLoading" style="width: 2rem; height: 2rem" strokeWidth="6" />

      <div v-else class="scan-content">
        <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>
        <MetricsTable :metrics="metrics" />
        <Divider />
        <SliceViewer :case-id="caseId" :initial-slice="60" />
      </div>
    </Panel>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Divider from 'primevue/divider'
import Message from 'primevue/message'
import Panel from 'primevue/panel'
import ProgressSpinner from 'primevue/progressspinner'
import Tag from 'primevue/tag'

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
