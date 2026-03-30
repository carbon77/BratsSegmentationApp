<template>
  <div class="rounded-xl border border-cyan-500/30 bg-slate-800/70 p-4">
    <h3 class="mb-3 text-lg font-medium text-cyan-200">Segmentation slice</h3>

    <div class="mb-4 flex flex-wrap items-end gap-3">
      <div>
        <label class="mb-2 block text-sm text-slate-300">Slice index</label>
        <InputNumber
          v-model="localSliceIdx"
          :min="0"
          inputId="sliceIdx"
          inputClass="!bg-slate-900 !text-cyan-100 !border-cyan-600/60"
        />
      </div>

      <Button
        label="Load image"
        icon="pi pi-image"
        :loading="isLoading"
        class="!bg-cyan-600 !border-cyan-500 hover:!bg-cyan-500"
        @click="loadImage"
      />
      <Button
        label="Download image"
        icon="pi pi-download"
        severity="secondary"
        :loading="isDownloading"
        :disabled="!imageSrc"
        class="!border-violet-400 !text-violet-200"
        outlined
        @click="downloadImage"
      />
    </div>

    <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>

    <div v-if="imageSrc" class="rounded-lg border border-slate-700 bg-slate-950 p-2">
      <img :src="imageSrc" alt="Segmentation mask slice" class="mx-auto max-h-[500px] rounded" />
    </div>
    <p v-else class="text-slate-400">Load a slice image to preview segmentation mask.</p>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import Message from 'primevue/message'

import { downloadSlice } from '../../services/api'

const props = defineProps({
  caseId: {
    type: String,
    required: true
  },
  initialSlice: {
    type: Number,
    default: 60
  }
})

const localSliceIdx = ref(props.initialSlice)
const imageSrc = ref('')
const isLoading = ref(false)
const isDownloading = ref(false)
const errorMessage = ref('')

function clearObjectUrl() {
  if (imageSrc.value) {
    URL.revokeObjectURL(imageSrc.value)
    imageSrc.value = ''
  }
}

async function loadImage() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const blob = await downloadSlice(props.caseId, localSliceIdx.value ?? 0)
    clearObjectUrl()
    imageSrc.value = URL.createObjectURL(blob)
  } catch {
    errorMessage.value = 'Unable to load slice image.'
  } finally {
    isLoading.value = false
  }
}

function downloadImage() {
  if (!imageSrc.value) return

  isDownloading.value = true
  const link = document.createElement('a')
  link.href = imageSrc.value
  link.download = `${props.caseId}-slice-${localSliceIdx.value ?? 0}.png`
  link.click()
  isDownloading.value = false
}

onMounted(loadImage)
onUnmounted(clearObjectUrl)
</script>
