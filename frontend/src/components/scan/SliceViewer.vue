<template>
  <Panel header="Segmentation slice">
    <div class="slice-controls">
      <div class="field-block">
        <label for="sliceIdx">Slice index</label>
        <InputNumber v-model="localSliceIdx" :min="0" inputId="sliceIdx" />
      </div>
      <div class="field-block field-block--wide">
        <label for="sliceSlider">Quick adjust</label>
        <Slider id="sliceSlider" v-model="localSliceIdx" :min="0" :max="155" />
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
      <Image :src="imageSrc" alt="Segmentation mask slice" preview imageClass="slice-image" />
    </div>
    <Message v-else severity="warn">Load a slice image to preview segmentation mask.</Message>
  </Panel>
</template>

<script setup>
import { onUnmounted, ref } from 'vue'
import Button from 'primevue/button'
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

onUnmounted(clearObjectUrl)
</script>
