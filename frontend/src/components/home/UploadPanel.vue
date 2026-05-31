<template>
  <Panel :header="t('uploadPanelTitle')" toggleable>
    <Panel :header="t('automaticAssignment')">
      <Message severity="info">{{ t('automaticAssignmentCaption') }}</Message>
      <FileUpload
        mode="basic"
        customUpload
        multiple
        accept=".nii,.nii.gz"
        :chooseLabel="t('chooseFourFiles')"
        chooseIcon="pi pi-folder-open"
        @select="onAllFilesSelected"
      />
    </Panel>

    <Divider />

    <Panel :header="t('requiredModalities')">
      <DataTable :value="requiredRows" size="small" responsiveLayout="scroll">
        <Column field="label" :header="t('title')" />
        <Column :header="t('status')">
          <template #body="slotProps">
            <Tag
              :value="modelValue[slotProps.data.key] ? t('selected') : t('missing')"
              :severity="modelValue[slotProps.data.key] ? 'success' : 'warning'"
            />
          </template>
        </Column>
        <Column :header="t('value')">
          <template #body="slotProps">
            {{ selectedName(slotProps.data.key) }}
          </template>
        </Column>
        <Column :header="t('actions')">
          <template #body="slotProps">
            <FileUpload
              mode="basic"
              customUpload
              accept=".nii,.nii.gz"
              :chooseLabel="modelValue[slotProps.data.key] ? t('replace') : t('choose')"
              chooseIcon="pi pi-upload"
              @select="(event) => onFileSelected(event, slotProps.data.key)"
            />
          </template>
        </Column>
      </DataTable>
    </Panel>

    <Divider />

    <Panel :header="t('optionalTrueMask')">
      <DataTable :value="optionalRows" size="small" responsiveLayout="scroll">
        <Column field="label" :header="t('title')" />
        <Column :header="t('status')">
          <template #body="slotProps">
            <Tag
              :value="modelValue[slotProps.data.key] ? t('selected') : t('optional')"
              :severity="modelValue[slotProps.data.key] ? 'success' : 'info'"
            />
          </template>
        </Column>
        <Column :header="t('value')">
          <template #body="slotProps">
            {{ selectedName(slotProps.data.key) }}
          </template>
        </Column>
        <Column :header="t('actions')">
          <template #body="slotProps">
            <FileUpload
              mode="basic"
              customUpload
              accept=".nii,.nii.gz"
              :chooseLabel="modelValue[slotProps.data.key] ? t('replace') : t('choose')"
              chooseIcon="pi pi-upload"
              @select="(event) => onFileSelected(event, slotProps.data.key)"
            />
          </template>
        </Column>
      </DataTable>
    </Panel>

    <Divider />

    <Toolbar>
      <template #start>
        <Button
          :label="t('createScan')"
          icon="pi pi-cloud-upload"
          :loading="isUploading"
          :disabled="!allModalitiesSelected || isUploading"
          @click="$emit('submit')"
        />
      </template>
      <template #end>
        <Message severity="info">{{ t('allModalitiesRequired') }}</Message>
      </template>
    </Toolbar>

    <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>
  </Panel>
</template>

<script setup>
import { computed } from 'vue'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Divider from 'primevue/divider'
import FileUpload from 'primevue/fileupload'
import Message from 'primevue/message'
import Panel from 'primevue/panel'
import Tag from 'primevue/tag'
import Toolbar from 'primevue/toolbar'

import { usePreferences } from '../../services/preferences'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  isUploading: {
    type: Boolean,
    default: false
  },
  errorMessage: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'submit'])

const modalities = ['t1', 't1ce', 't2', 'flair']
const { t } = usePreferences()

const requiredRows = computed(() => modalities.map((key) => ({ key, label: key.toUpperCase() })))
const optionalRows = [{ key: 'true_mask', label: 'TRUE_MASK' }]
const allModalitiesSelected = computed(() => modalities.every((m) => Boolean(props.modelValue[m])))

function updateFile(modality, file) {
  emit('update:modelValue', {
    ...props.modelValue,
    [modality]: file ?? null
  })
}

function filesFromEvent(event) {
  return Array.from(event.files ?? event.originalEvent?.target?.files ?? [])
}

function onFileSelected(event, modality) {
  const [file] = filesFromEvent(event)
  updateFile(modality, file)
}

function detectModality(filename) {
  const normalized = filename.toLowerCase()
  if (normalized.includes('t1ce')) return 't1ce'
  if (normalized.includes('flair')) return 'flair'
  if (normalized.includes('t2')) return 't2'
  if (normalized.includes('t1')) return 't1'
  return null
}

function onAllFilesSelected(event) {
  const files = filesFromEvent(event)
  const nextValue = { ...props.modelValue }

  files.forEach((file) => {
    const modality = detectModality(file.name)
    if (modality) nextValue[modality] = file
  })

  emit('update:modelValue', nextValue)
}

function selectedName(modality) {
  return props.modelValue[modality]?.name ?? t('noFileSelected')
}
</script>
