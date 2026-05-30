<template>
  <Panel :header="t('segmentationSlice')">
    <Toolbar>
      <template #start>
        <InputGroup>
          <InputGroupAddon>{{ t('sliceIndex') }}</InputGroupAddon>
          <InputNumber v-model="localSliceIdx" :min="0" :max="maxSliceIdx" inputId="sliceIdx" />
        </InputGroup>
      </template>
      <template #end>
        <Dropdown
          id="overlayModality"
          v-model="overlayModality"
          :options="overlayOptions"
          optionLabel="label"
          optionValue="value"
          :placeholder="t('chooseModality')"
        />
        <Button :label="t('loadSlice')" icon="pi pi-refresh" :loading="isLoading" @click="loadImages" />
      </template>
    </Toolbar>

    <Panel :header="t('quickAdjust')">
      <Slider id="sliceSlider" v-model="localSliceIdx" :min="0" :max="maxSliceIdx" />
    </Panel>

    <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>

    <ProgressSpinner v-if="isLoading && !plainImageSrc && !maskedImageSrc" style="width: 2rem; height: 2rem" strokeWidth="6" />

    <Splitter v-else style="min-height: 32rem">
      <SplitterPanel :size="50" :min-size="35">
        <Panel :header="t('sliceWithoutMask')">
          <Image v-if="plainImageSrc" :src="plainImageSrc" :alt="plainImageAlt" preview :imageStyle="imageStyle" />
          <Message v-else severity="warn">{{ t('loadSlicePrompt') }}</Message>
          <template #footer>
            <Button
              :label="t('downloadPng')"
              icon="pi pi-download"
              severity="secondary"
              :loading="isDownloadingPlain"
              :disabled="!plainImageSrc"
              outlined
              @click="downloadImage('plain')"
            />
          </template>
        </Panel>
      </SplitterPanel>

      <SplitterPanel :size="50" :min-size="35">
        <Panel :header="t('sliceWithMask')">
          <Image v-if="maskedImageSrc" :src="maskedImageSrc" :alt="maskedImageAlt" preview :imageStyle="imageStyle" />
          <Message v-else severity="warn">{{ t('loadSlicePrompt') }}</Message>
          <template #footer>
            <Button
              :label="t('downloadPng')"
              icon="pi pi-download"
              severity="secondary"
              :loading="isDownloadingMasked"
              :disabled="!maskedImageSrc"
              outlined
              @click="downloadImage('masked')"
            />
          </template>
        </Panel>
      </SplitterPanel>
    </Splitter>
  </Panel>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import Image from 'primevue/image'
import InputGroup from 'primevue/inputgroup'
import InputGroupAddon from 'primevue/inputgroupaddon'
import InputNumber from 'primevue/inputnumber'
import Message from 'primevue/message'
import Panel from 'primevue/panel'
import ProgressSpinner from 'primevue/progressspinner'
import Slider from 'primevue/slider'
import Splitter from 'primevue/splitter'
import SplitterPanel from 'primevue/splitterpanel'
import Toolbar from 'primevue/toolbar'

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
const overlayValues = ['t1', 't1ce', 't2', 'flair']
const imageStyle = { width: '100%', display: 'block' }
let requestId = 0

const overlayOptions = computed(() => overlayValues.map((value) => ({
  label: value.toUpperCase(),
  value
})))

const localSliceIdx = ref(props.initialSlice)
const overlayModality = ref('t1')
const plainImageSrc = ref('')
const maskedImageSrc = ref('')
const isLoading = ref(false)
const isDownloadingPlain = ref(false)
const isDownloadingMasked = ref(false)
const errorMessage = ref('')

const plainImageAlt = computed(() => t('plainSliceAlt', { modality: overlayModality.value.toUpperCase() }))
const maskedImageAlt = computed(() => t('overlaySliceAlt', { modality: overlayModality.value.toUpperCase() }))

function revokeObjectUrl(url) {
  if (url) URL.revokeObjectURL(url)
}

function clearObjectUrls() {
  revokeObjectUrl(plainImageSrc.value)
  revokeObjectUrl(maskedImageSrc.value)
  plainImageSrc.value = ''
  maskedImageSrc.value = ''
}

async function loadImages() {
  const currentRequestId = ++requestId
  isLoading.value = true
  errorMessage.value = ''

  try {
    const sliceIdx = localSliceIdx.value ?? 0
    const [plainBlob, maskedBlob] = await Promise.all([
      downloadSlice(props.caseId, sliceIdx, overlayModality.value, false),
      downloadSlice(props.caseId, sliceIdx, overlayModality.value, true)
    ])

    if (currentRequestId !== requestId) return

    const nextPlainUrl = URL.createObjectURL(plainBlob)
    const nextMaskedUrl = URL.createObjectURL(maskedBlob)
    clearObjectUrls()
    plainImageSrc.value = nextPlainUrl
    maskedImageSrc.value = nextMaskedUrl
  } catch {
    if (currentRequestId === requestId) {
      clearObjectUrls()
      errorMessage.value = t('sliceLoadFailed')
    }
  } finally {
    if (currentRequestId === requestId) isLoading.value = false
  }
}

function downloadImage(kind) {
  const isPlain = kind === 'plain'
  const imageSrc = isPlain ? plainImageSrc.value : maskedImageSrc.value
  if (!imageSrc) return

  if (isPlain) isDownloadingPlain.value = true
  else isDownloadingMasked.value = true

  const maskSuffix = isPlain ? 'without-mask' : 'with-mask'
  const link = document.createElement('a')
  link.href = imageSrc
  link.download = `${props.caseId}-slice-${localSliceIdx.value ?? 0}-${overlayModality.value}-${maskSuffix}.png`
  link.click()

  if (isPlain) isDownloadingPlain.value = false
  else isDownloadingMasked.value = false
}

watch([localSliceIdx, overlayModality], loadImages)

onMounted(loadImages)
onUnmounted(() => {
  requestId += 1
  clearObjectUrls()
})
</script>
