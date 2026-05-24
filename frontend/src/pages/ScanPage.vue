<template>
  <section>
    <Panel>
      <template #header>
        <div class="scan-header">
          <Tag :value="title || t('scanFallback', { caseId })" severity="info" />
          <div class="title-editor">
            <InputText v-model="editedTitle" :placeholder="t('scanTitlePlaceholder')" />
            <Button
              :label="t('saveTitle')"
              icon="pi pi-check"
              size="small"
              :disabled="!editedTitle.trim() || editedTitle === title"
              :loading="isSavingTitle"
              @click="saveTitle"
            />
          </div>
          <div class="scan-actions">
            <Button :label="t('downloadJson')" icon="pi pi-download" outlined size="small" @click="downloadMetricsJson" />
            <Button :label="t('downloadCsv')" icon="pi pi-file" outlined size="small" @click="downloadMetricsCsv" />
            <Button
              :label="t('deleteScan')"
              icon="pi pi-trash"
              severity="danger"
              outlined
              :loading="isDeleting"
              @click="removeScan"
            />
          </div>
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
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Panel from 'primevue/panel'
import ProgressSpinner from 'primevue/progressspinner'
import Tag from 'primevue/tag'

import MetricsTable from '../components/scan/MetricsTable.vue'
import SliceViewer from '../components/scan/SliceViewer.vue'
import { deleteScan, fetchMetrics, fetchScans, patchScanTitle } from '../services/api'
import { usePreferences } from '../services/preferences'

const props = defineProps({
  caseId: {
    type: String,
    required: true
  }
})

const router = useRouter()
const metrics = ref({})
const title = ref('')
const editedTitle = ref('')
const isLoading = ref(false)
const isDeleting = ref(false)
const isSavingTitle = ref(false)
const errorMessage = ref('')
const { t } = usePreferences()

function downloadBlob(filename, content, mimeType) {
  const blob = new Blob([content], { type: mimeType })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}

function flattenMetrics(node, prefix = '', rows = []) {
  if (node === null || node === undefined) {
    rows.push([prefix, ''])
    return rows
  }

  if (typeof node !== 'object') {
    rows.push([prefix, node])
    return rows
  }

  Object.entries(node).forEach(([key, value]) => {
    const nextPrefix = prefix ? `${prefix}.${key}` : key
    flattenMetrics(value, nextPrefix, rows)
  })

  return rows
}

function downloadMetricsJson() {
  const filename = `${props.caseId}-metrics.json`
  const payload = JSON.stringify({ case_id: props.caseId, metrics: metrics.value }, null, 2)
  downloadBlob(filename, payload, 'application/json;charset=utf-8')
}

function downloadMetricsCsv() {
  const rows = flattenMetrics(metrics.value)
  const csv = ['metric,value', ...rows.map(([metric, value]) => `${metric},${JSON.stringify(value)}`)].join('\n')
  downloadBlob(`${props.caseId}-metrics.csv`, csv, 'text/csv;charset=utf-8')
}

async function loadTitle() {
  try {
    const scans = await fetchScans()
    const currentScan = scans.find((scan) => scan.case_id === props.caseId)
    title.value = currentScan?.title || t('scanFallback', { caseId: props.caseId })
    editedTitle.value = title.value
  } catch {
    title.value = props.caseId
    editedTitle.value = props.caseId
  }
}

async function loadMetrics() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const payload = await fetchMetrics(props.caseId)
    metrics.value = payload.metrics ?? {}
  } catch {
    errorMessage.value = t('metricsLoadFailed')
  } finally {
    isLoading.value = false
  }
}

async function saveTitle() {
  const nextTitle = editedTitle.value.trim()
  if (!nextTitle) return

  isSavingTitle.value = true
  errorMessage.value = ''
  try {
    await patchScanTitle(props.caseId, nextTitle)
    title.value = nextTitle
  } catch {
    errorMessage.value = t('titleUpdateFailed')
  } finally {
    isSavingTitle.value = false
  }
}

async function removeScan() {
  isDeleting.value = true
  errorMessage.value = ''

  try {
    await deleteScan(props.caseId)
    await router.push('/')
  } catch {
    errorMessage.value = t('currentScanDeleteFailed')
  } finally {
    isDeleting.value = false
  }
}

onMounted(loadMetrics)
onMounted(loadTitle)
</script>
