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
            <Dropdown
              v-model="dicomModality"
              :options="modalityOptions"
              optionLabel="label"
              optionValue="value"
              :placeholder="t('chooseModality')"
              class="modality-dropdown"
            />
            <Button
              :label="t('downloadDicom')"
              icon="pi pi-file-export"
              outlined
              size="small"
              :loading="isConvertingDicom"
              :disabled="!dicomModality || isSendingOrthanc"
              @click="downloadDicom"
            />
            <Button
              :label="t('sendDicomToOrthanc')"
              icon="pi pi-send"
              outlined
              size="small"
              :loading="isSendingOrthanc"
              :disabled="!dicomModality || isConvertingDicom"
              @click="sendToOrthanc"
            />
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
        <Message v-if="metadataSavedMessage" severity="success">{{ metadataSavedMessage }}</Message>
        <Message v-if="orthancMessage" severity="success">{{ orthancMessage }}</Message>

        <section class="metadata-panel" aria-labelledby="dicom-metadata-title">
          <div>
            <h3 id="dicom-metadata-title" class="section-title">{{ t('dicomMetadata') }}</h3>
            <p class="section-caption">{{ t('dicomMetadataCaption') }}</p>
          </div>
          <div class="metadata-form">
            <label v-for="field in metadataFields" :key="field.key" class="field-block">
              <span>{{ t(field.labelKey) }}</span>
              <Dropdown
                v-if="field.type === 'select'"
                v-model="editedDicomMetadata[field.key]"
                :options="field.options"
                optionLabel="label"
                optionValue="value"
                :placeholder="t('dicomMetadataEmpty')"
                showClear
              />
              <InputText
                v-else
                v-model="editedDicomMetadata[field.key]"
                :type="field.type || 'text'"
                :placeholder="t('dicomMetadataEmpty')"
              />
            </label>
          </div>
          <div class="metadata-actions">
            <Button
              :label="t('saveDicomMetadata')"
              icon="pi pi-save"
              size="small"
              :loading="isSavingMetadata"
              @click="saveDicomMetadata"
            />
          </div>
        </section>

        <MetricsTable :metrics="metrics" />
        <Divider />
        <SliceViewer :case-id="caseId" :initial-slice="60" />
      </div>
    </Panel>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Divider from 'primevue/divider'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Panel from 'primevue/panel'
import ProgressSpinner from 'primevue/progressspinner'
import Tag from 'primevue/tag'

import MetricsTable from '../components/scan/MetricsTable.vue'
import SliceViewer from '../components/scan/SliceViewer.vue'
import { deleteScan, downloadDicomArchive, fetchMetrics, fetchScan, fetchScans, patchScanTitle, sendDicomToOrthanc, updateDicomMetadata } from '../services/api'
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
const isSavingMetadata = ref(false)
const isConvertingDicom = ref(false)
const isSendingOrthanc = ref(false)
const dicomModality = ref('t1')
const errorMessage = ref('')
const metadataSavedMessage = ref('')
const orthancMessage = ref('')
const { t } = usePreferences()
const modalities = ['t1', 't1ce', 't2', 'flair']
const modalityOptions = modalities.map((modality) => ({
  label: modality.toUpperCase(),
  value: modality
}))
const sexOptions = [
  { label: t('dicomPatientSexMale'), value: 'M' },
  { label: t('dicomPatientSexFemale'), value: 'F' },
  { label: t('dicomPatientSexOther'), value: 'O' }
]
const metadataFields = [
  { key: 'patient_name', labelKey: 'dicomPatientName' },
  { key: 'patient_id', labelKey: 'dicomPatientId' },
  { key: 'patient_birth_date', labelKey: 'dicomPatientBirthDate', type: 'date' },
  { key: 'patient_sex', labelKey: 'dicomPatientSex', type: 'select', options: sexOptions },
  { key: 'accession_number', labelKey: 'dicomAccessionNumber' },
  { key: 'study_id', labelKey: 'dicomStudyId' },
  { key: 'study_date', labelKey: 'dicomStudyDate', type: 'date' },
  { key: 'study_description', labelKey: 'dicomStudyDescription' },
  { key: 'series_description', labelKey: 'dicomSeriesDescription' },
  { key: 'institution_name', labelKey: 'dicomInstitutionName' },
  { key: 'referring_physician_name', labelKey: 'dicomReferringPhysicianName' }
]
const editedDicomMetadata = reactive(createEmptyDicomMetadata())

function createEmptyDicomMetadata() {
  return {
    patient_name: '',
    patient_id: '',
    patient_birth_date: '',
    patient_sex: '',
    accession_number: '',
    study_id: '',
    study_date: '',
    study_description: '',
    series_description: '',
    institution_name: '',
    referring_physician_name: ''
  }
}

function assignDicomMetadata(metadata = {}) {
  Object.keys(editedDicomMetadata).forEach((key) => {
    editedDicomMetadata[key] = metadata?.[key] ?? ''
  })
}

function dicomMetadataPayload() {
  return Object.fromEntries(
    Object.entries(editedDicomMetadata).map(([key, value]) => [key, typeof value === 'string' ? value.trim() : value])
  )
}

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

async function downloadDicom() {
  if (!dicomModality.value) return

  isConvertingDicom.value = true
  errorMessage.value = ''
  try {
    const blob = await downloadDicomArchive(props.caseId, dicomModality.value)
    const filename = `${props.caseId}-${dicomModality.value}-dicom.zip`
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename
    link.click()
    URL.revokeObjectURL(link.href)
  } catch {
    errorMessage.value = t('dicomConversionFailed')
  } finally {
    isConvertingDicom.value = false
  }
}

async function sendToOrthanc() {
  if (!dicomModality.value) return

  isSendingOrthanc.value = true
  errorMessage.value = ''
  orthancMessage.value = ''
  try {
    const result = await sendDicomToOrthanc(props.caseId, dicomModality.value)
    orthancMessage.value = t('dicomOrthancSent', { count: result.instances_uploaded })
  } catch {
    errorMessage.value = t('dicomOrthancFailed')
  } finally {
    isSendingOrthanc.value = false
  }
}

async function loadScanDetails() {
  try {
    const currentScan = await fetchScan(props.caseId)
    title.value = currentScan?.title || t('scanFallback', { caseId: props.caseId })
    editedTitle.value = title.value
    assignDicomMetadata(currentScan?.dicom_metadata)
  } catch {
    try {
      const scans = await fetchScans()
      const currentScan = scans.find((scan) => scan.case_id === props.caseId)
      title.value = currentScan?.title || t('scanFallback', { caseId: props.caseId })
      editedTitle.value = title.value
      assignDicomMetadata(currentScan?.dicom_metadata)
    } catch {
      title.value = props.caseId
      editedTitle.value = props.caseId
    }
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

async function saveDicomMetadata() {
  isSavingMetadata.value = true
  errorMessage.value = ''
  metadataSavedMessage.value = ''
  try {
    await updateDicomMetadata(props.caseId, dicomMetadataPayload())
    metadataSavedMessage.value = t('dicomMetadataSaved')
  } catch {
    errorMessage.value = t('dicomMetadataUpdateFailed')
  } finally {
    isSavingMetadata.value = false
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
onMounted(loadScanDetails)
</script>
