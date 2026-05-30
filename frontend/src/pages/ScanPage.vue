<template>
  <section>
    <Card>
      <template #title>
        <Tag :value="title || t('scanFallback', { caseId })" severity="info" />
      </template>
      <template #subtitle>
        <InputGroup>
          <InputText v-model="editedTitle" :placeholder="t('scanTitlePlaceholder')" />
          <Button
            :label="t('saveTitle')"
            icon="pi pi-check"
            :disabled="!editedTitle.trim() || editedTitle === title"
            :loading="isSavingTitle"
            @click="saveTitle"
          />
          <Button
            :label="t('deleteScan')"
            icon="pi pi-trash"
            severity="danger"
            outlined
            :loading="isDeleting"
            @click="removeScan"
          />
        </InputGroup>
      </template>
      <template #content>
        <ProgressSpinner v-if="isLoading" style="width: 2rem; height: 2rem" strokeWidth="6" />

        <div v-else>
          <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>
          <Message v-if="metadataSavedMessage" severity="success">{{ metadataSavedMessage }}</Message>
          <Message v-if="orthancMessage" severity="success">{{ orthancMessage }}</Message>

          <Splitter style="min-height: 42rem">
            <SplitterPanel :size="18" :min-size="15">
              <Menu :model="sectionMenuItems" />
            </SplitterPanel>

            <SplitterPanel :size="55" :min-size="35">
              <Panel v-if="activeSection === 'slices'" :header="t('segmentationSlice')">
                <SliceViewer :case-id="caseId" :initial-slice="60" />
              </Panel>

              <Panel v-else-if="activeSection === 'metrics'" :header="t('metrics')">
                <MetricsTable :metrics="metrics" />
              </Panel>

              <Panel v-else :header="t('dicomMetadata')">
                <p>{{ t('dicomMetadataCaption') }}</p>
                <DataTable :value="metadataFields" size="small" responsiveLayout="scroll">
                  <Column :header="t('metric')">
                    <template #body="slotProps">
                      {{ t(slotProps.data.labelKey) }}
                    </template>
                  </Column>
                  <Column :header="t('value')">
                    <template #body="slotProps">
                      <Dropdown
                        v-if="slotProps.data.type === 'select'"
                        v-model="editedDicomMetadata[slotProps.data.key]"
                        :options="slotProps.data.options"
                        optionLabel="label"
                        optionValue="value"
                        :placeholder="t('dicomMetadataEmpty')"
                        showClear
                      />
                      <InputText
                        v-else
                        v-model="editedDicomMetadata[slotProps.data.key]"
                        :type="slotProps.data.type || 'text'"
                        :placeholder="t('dicomMetadataEmpty')"
                      />
                    </template>
                  </Column>
                </DataTable>
              </Panel>
            </SplitterPanel>

            <SplitterPanel :size="27" :min-size="22">
              <Panel v-if="activeSection === 'slices'" :header="t('sectionSettings')">
                <Fieldset :legend="t('dicomExportSettings')">
                  <Dropdown
                    v-model="dicomModality"
                    :options="modalityOptions"
                    optionLabel="label"
                    optionValue="value"
                    :placeholder="t('chooseModality')"
                  />
                  <Button
                    :label="t('downloadDicom')"
                    icon="pi pi-file-export"
                    outlined
                    :loading="isConvertingDicom"
                    :disabled="!dicomModality || isSendingOrthanc"
                    @click="downloadDicom"
                  />
                  <Button
                    :label="t('sendDicomToOrthanc')"
                    icon="pi pi-send"
                    outlined
                    :loading="isSendingOrthanc"
                    :disabled="!dicomModality || isConvertingDicom"
                    @click="sendToOrthanc"
                  />
                </Fieldset>
              </Panel>

              <Panel v-else-if="activeSection === 'metrics'" :header="t('sectionSettings')">
                <Fieldset :legend="t('metricsExportSettings')">
                  <Button :label="t('downloadJson')" icon="pi pi-download" outlined @click="downloadMetricsJson" />
                  <Button :label="t('downloadCsv')" icon="pi pi-file" outlined @click="downloadMetricsCsv" />
                </Fieldset>
              </Panel>

              <Panel v-else :header="t('sectionSettings')">
                <Fieldset :legend="t('metadataSettings')">
                  <Button
                    :label="t('saveDicomMetadata')"
                    icon="pi pi-save"
                    :loading="isSavingMetadata"
                    @click="saveDicomMetadata"
                  />
                </Fieldset>
              </Panel>
            </SplitterPanel>
          </Splitter>
        </div>
      </template>
    </Card>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dropdown from 'primevue/dropdown'
import Fieldset from 'primevue/fieldset'
import InputGroup from 'primevue/inputgroup'
import InputText from 'primevue/inputtext'
import Menu from 'primevue/menu'
import Message from 'primevue/message'
import Panel from 'primevue/panel'
import ProgressSpinner from 'primevue/progressspinner'
import Splitter from 'primevue/splitter'
import SplitterPanel from 'primevue/splitterpanel'
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
const activeSection = ref('slices')
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

const sectionMenuItems = computed(() => [
  {
    label: t('slicesSection'),
    icon: activeSection.value === 'slices' ? 'pi pi-check' : 'pi pi-images',
    command: () => { activeSection.value = 'slices' }
  },
  {
    label: t('metricsSection'),
    icon: activeSection.value === 'metrics' ? 'pi pi-check' : 'pi pi-chart-bar',
    command: () => { activeSection.value = 'metrics' }
  },
  {
    label: t('metadataSection'),
    icon: activeSection.value === 'metadata' ? 'pi pi-check' : 'pi pi-id-card',
    command: () => { activeSection.value = 'metadata' }
  }
])

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
