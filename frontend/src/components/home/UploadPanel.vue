<template>
  <Card class="h-full">
    <template #title>
      <span class="text-cyan-200">Upload MRI modalities</span>
    </template>
    <template #content>
      <div class="space-y-4">
        <div class="rounded-xl border border-cyan-500/30 bg-slate-800/80 p-4">
          <div class="mb-3 flex items-center justify-between gap-4">
            <div>
              <p class="font-medium text-cyan-100">Select all modalities</p>
              <p class="text-xs text-slate-300">Choose four .nii files in one action.</p>
            </div>
            <Button label="Choose 4 files" icon="pi pi-folder-open" outlined @click="openAllPicker" />
          </div>
          <input
            ref="allInputRef"
            class="hidden"
            type="file"
            accept=".nii,.nii.gz"
            multiple
            @change="onAllFilesSelected"
          />
          <small class="text-slate-400">Matched by filename keywords: t1, t1ce, t2, flair.</small>
        </div>

        <div
          v-for="modality in modalities"
          :key="modality"
          class="rounded-xl border border-violet-500/30 bg-slate-800/70 p-4"
        >
          <div class="flex items-center justify-between gap-4">
            <div>
              <p class="font-medium uppercase tracking-wide text-violet-100">{{ modality }}</p>
              <p class="text-sm text-slate-300">{{ selectedName(modality) }}</p>
            </div>
            <Button
              :label="modelValue[modality] ? 'Replace file' : 'Choose file'"
              icon="pi pi-upload"
              outlined
              @click="openPicker(modality)"
            />
          </div>
          <input
            :ref="(el) => setFileInputRef(modality, el)"
            class="hidden"
            type="file"
            accept=".nii,.nii.gz"
            @change="onFileSelected($event, modality)"
          />
        </div>

        <div class="flex items-center gap-3">
          <Button
            label="Create scan"
            icon="pi pi-cloud-upload"
            :loading="isUploading"
            :disabled="!allModalitiesSelected || isUploading"
            @click="$emit('submit')"
          />
          <small class="text-slate-300">All 4 modalities are required.</small>
        </div>

        <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>
      </div>
    </template>
  </Card>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Message from 'primevue/message'

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
