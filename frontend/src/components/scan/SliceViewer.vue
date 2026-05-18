<template>
  <Panel :header="t('segmentationSlice')">
    <div class="slice-controls">
      <div class="field-block">
        <label for="sliceIdx">{{ t('sliceIndex') }}</label>
        <InputNumber v-model="localSliceIdx" :min="0" :max="maxSliceIdx" inputId="sliceIdx" />
      </div>
      <div class="field-block field-block--wide">
        <label for="sliceSlider">{{ t('quickAdjust') }}</label>
        <Slider id="sliceSlider" v-model="localSliceIdx" :min="0" :max="maxSliceIdx" />
      </div>
      <div class="field-block field-block--wide">
        <label for="overlayModality">{{ t('overlay') }}</label>
        <Dropdown
          id="overlayModality"
          v-model="overlayModality"
          :options="overlayOptions"
          optionLabel="label"
          optionValue="value"
          :placeholder="t('overlayMaskOnly')"
        />
      </div>
      <div class="button-row">
        <Button :label="t('loadSlice')" icon="pi pi-image" :loading="isLoading" @click="loadImage" />
        <Button
          :label="t('downloadPng')"
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
    <Message v-else severity="warn">{{ t('loadSlicePrompt') }}</Message>
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
import { usePreferences } from '../../services/preferences'

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

const { t } = usePreferences()
const maxSliceIdx = 95
const overlayValues = [null, 't1', 't1ce', 't2', 'flair']

const overlayOptions = computed(() => overlayValues.map((value) => ({
  label: value ? `${t('overlay')} ${value.toUpperCase()}` : t('overlayMaskOnly'),
  value
})))

const localSliceIdx = ref(props.initialSlice)
const overlayModality = ref(null)
const imageSrc = ref('')
const isLoading = ref(false)
const isDownloading = ref(false)
const errorMessage = ref('')

const imageAlt = computed(() => {
  if (!overlayModality.value) return t('maskSliceAlt')
  return t('overlaySliceAlt', { modality: overlayModality.value.toUpperCase() })
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
    errorMessage.value = t('sliceLoadFailed')
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
