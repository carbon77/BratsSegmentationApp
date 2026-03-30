<template>
  <section class="space-y-6">
    <Card>
      <template #title>Scan {{ caseId }}</template>
      <template #content>
        <div v-if="isLoading" class="py-4">
          <ProgressSpinner style="width: 34px; height: 34px" strokeWidth="6" />
        </div>

        <div v-else class="space-y-4">
          <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>

          <DataTable v-if="metricRows.length" :value="metricRows" size="small" responsiveLayout="scroll">
            <Column field="name" header="Metric" />
            <Column field="value" header="Value" />
          </DataTable>
          <p v-else class="text-slate-500">No metrics available.</p>

          <div class="rounded-lg border border-slate-200 p-4">
            <h3 class="mb-3 font-medium text-slate-800">Segmentation mask slice image</h3>

            <div class="flex flex-wrap items-end gap-3">
              <div>
                <label class="mb-2 block text-sm text-slate-600">Slice index</label>
                <InputNumber v-model="sliceIdx" :min="0" inputId="sliceIdx" />
              </div>

              <Button
                label="Download image"
                icon="pi pi-download"
                :loading="isDownloading"
                @click="downloadImage"
              />
            </div>
          </div>
        </div>
      </template>
    </Card>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import InputNumber from 'primevue/inputnumber'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'

import { downloadSlice, fetchMetrics } from '../services/api'

const props = defineProps({
  caseId: {
    type: String,
    required: true
  }
})

const metrics = ref({})
const isLoading = ref(false)
const isDownloading = ref(false)
const errorMessage = ref('')
const sliceIdx = ref(60)

const metricRows = computed(() =>
  Object.entries(metrics.value).map(([name, value]) => ({
    name,
    value: typeof value === 'number' ? value.toFixed(4) : String(value)
  }))
)

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

async function downloadImage() {
  isDownloading.value = true
  errorMessage.value = ''

  try {
    const blob = await downloadSlice(props.caseId, sliceIdx.value ?? 0)
    const imageUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = imageUrl
    link.download = `${props.caseId}-slice-${sliceIdx.value ?? 0}.png`
    link.click()
    URL.revokeObjectURL(imageUrl)
  } catch {
    errorMessage.value = 'Unable to download slice image.'
  } finally {
    isDownloading.value = false
  }
}

onMounted(loadMetrics)
</script>
