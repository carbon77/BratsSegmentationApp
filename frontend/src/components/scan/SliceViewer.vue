<template>
  <Panel header="Segmentation slice">
    <div class="slice-controls">
      <div class="field-block">
        <label for="sliceIdx">Slice index</label>
        <InputNumber v-model="localSliceIdx" :min="0" :max="maxSliceIdx" inputId="sliceIdx" />
      </div>
      <div class="field-block field-block--wide">
        <label for="sliceSlider">Quick adjust</label>
        <Slider id="sliceSlider" v-model="localSliceIdx" :min="0" :max="maxSliceIdx" />
      </div>
      <div class="field-block field-block--wide">
        <label for="overlayModality">MRI scan cover</label>
        <Dropdown
          id="overlayModality"
          v-model="overlayModality"
          :options="overlayOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Mask only"
        />
      </div>
      <div class="button-row">
        <Button label="Load image" icon="pi pi-image" :loading="isLoading" @click="loadImage" />
        <Button
          label="Download image"
          icon="pi pi-download"
          severity="secondary"
          :loading="isDownloading"
          :disabled="!imageSrc"
          outlined
          @click="downloadImage"
        />
      </div>
    </div>

    <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>

    <div v-if="imageSrc" class="image-wrapper">
      <Image :src="imageSrc" :alt="imageAlt" preview imageClass="slice-image" />
    </div>
    <Message v-else severity="warn">Load a slice image to preview segmentation mask.</Message>
  </Panel>
</template>

<script setup>
import { computed, onUnmounted, ref, watch } from 'vue'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import Image from 'primevue/image'
import InputNumber from 'primevue/inputnumber'
import Message from 'primevue/message'
import Panel from 'primevue/panel'
import Slider from 'primevue/slider'

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

const maxSliceIdx = 95
const overlayOptions = [
  { label: 'Do not cover (mask only)', value: null },
  { label: 'Cover T1 scan', value: 't1' },
  { label: 'Cover T1CE scan', value: 't1ce' },
  { label: 'Cover T2 scan', value: 't2' },
  { label: 'Cover FLAIR scan', value: 'flair' }
]

const localSliceIdx = ref(props.initialSlice)
const overlayModality = ref(null)
const imageSrc = ref('')
const isLoading = ref(false)
const isDownloading = ref(false)
const errorMessage = ref('')

const imageAlt = computed(() => {
  if (!overlayModality.value) return 'Segmentation mask slice'
  return `Segmentation mask slice covered with ${overlayModality.value.toUpperCase()} MRI scan`
})

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
    const sliceIdx = localSliceIdx.value ?? 0
    const blob = await downloadSlice(props.caseId, sliceIdx, overlayModality.value)
    clearObjectUrl()
    imageSrc.value = URL.createObjectURL(blob)
  } catch {
    clearObjectUrl()
    errorMessage.value = 'Unable to load slice image.'
  } finally {
    isLoading.value = false
  }
}

function downloadImage() {
  if (!imageSrc.value) return

  const overlaySuffix = overlayModality.value ? `-${overlayModality.value}-cover` : '-mask-only'
  isDownloading.value = true
  const link = document.createElement('a')
  link.href = imageSrc.value
  link.download = `${props.caseId}-slice-${localSliceIdx.value ?? 0}${overlaySuffix}.png`
  link.click()
  isDownloading.value = false
}

watch([localSliceIdx, overlayModality], () => {
  clearObjectUrl()
  errorMessage.value = ''
})

onUnmounted(clearObjectUrl)
</script>
