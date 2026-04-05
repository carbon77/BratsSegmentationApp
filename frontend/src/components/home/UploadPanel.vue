<template>
  <Panel header="Upload MRI modalities" toggleable>
    <div class="upload-panel-content">
      <Fieldset legend="Automatic assignment" class="section-block">
        <p class="section-caption">Select 4 files in one action; filenames are mapped by keywords: t1, t1ce, t2, flair.</p>
        <Button label="Choose 4 files" icon="pi pi-folder-open" @click="openAllPicker" />
        <input
          ref="allInputRef"
          class="hidden-input"
          type="file"
          accept=".nii,.nii.gz"
          multiple
          @change="onAllFilesSelected"
        />
      </Fieldset>

      <Fieldset legend="Required modalities" class="section-block">
        <div class="modality-grid">
          <div v-for="modality in modalities" :key="modality" class="modality-row">
            <div>
              <div class="modality-label">{{ modality.toUpperCase() }}</div>
              <small class="modality-name">{{ selectedName(modality) }}</small>
            </div>
            <div class="row-actions">
              <Tag :value="modelValue[modality] ? 'Selected' : 'Missing'" :severity="modelValue[modality] ? 'success' : 'warning'" />
              <Button
                :label="modelValue[modality] ? 'Replace' : 'Choose'"
                icon="pi pi-upload"
                outlined
                @click="openPicker(modality)"
              />
              <input
                :ref="(el) => setFileInputRef(modality, el)"
                class="hidden-input"
                type="file"
                accept=".nii,.nii.gz"
                @change="onFileSelected($event, modality)"
              />
            </div>
          </div>
        </div>
      </Fieldset>

      <Fieldset legend="Optional true mask" class="section-block">
        <div class="modality-row">
          <div>
            <div class="modality-label">TRUE_MASK</div>
            <small class="modality-name">{{ selectedName('true_mask') }}</small>
          </div>
          <div class="row-actions">
            <Tag :value="modelValue.true_mask ? 'Selected' : 'Optional'" :severity="modelValue.true_mask ? 'success' : 'info'" />
            <Button
              :label="modelValue.true_mask ? 'Replace' : 'Choose'"
              icon="pi pi-upload"
              outlined
              @click="openPicker('true_mask')"
            />
          </div>
        </div>
        <input
          :ref="(el) => setFileInputRef('true_mask', el)"
          class="hidden-input"
          type="file"
          accept=".nii,.nii.gz"
          @change="onFileSelected($event, 'true_mask')"
        />
      </Fieldset>

      <div class="submit-row">
        <Button
          label="Create scan"
          icon="pi pi-cloud-upload"
          :loading="isUploading"
          :disabled="!allModalitiesSelected || isUploading"
          @click="$emit('submit')"
        />
        <small>All 4 modalities are required for upload.</small>
      </div>

      <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>
    </div>
  </Panel>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import Button from 'primevue/button'
import Fieldset from 'primevue/fieldset'
import Message from 'primevue/message'
import Panel from 'primevue/panel'
import Tag from 'primevue/tag'

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
const inputRefs = reactive({})
const allInputRef = ref(null)

const allModalitiesSelected = computed(() => modalities.every((m) => Boolean(props.modelValue[m])))

function updateFile(modality, file) {
  emit('update:modelValue', {
    ...props.modelValue,
    [modality]: file ?? null
  })
}

function setFileInputRef(modality, element) {
  if (element) inputRefs[modality] = element
}

function openPicker(modality) {
  inputRefs[modality]?.click()
}

function openAllPicker() {
  allInputRef.value?.click()
}

function onFileSelected(event, modality) {
  const [file] = event.target.files
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
  const files = Array.from(event.target.files ?? [])
  const nextValue = { ...props.modelValue }

  files.forEach((file) => {
    const modality = detectModality(file.name)
    if (modality) nextValue[modality] = file
  })

  emit('update:modelValue', nextValue)
}

function selectedName(modality) {
  return props.modelValue[modality]?.name ?? 'No file selected'
}
</script>
