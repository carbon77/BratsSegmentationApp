<template>
  <section class="home-page">
    <Message v-if="pageError" severity="error">{{ pageError }}</Message>

    <Splitter class="home-splitter">
      <SplitterPanel :size="55" :min-size="40">
        <UploadPanel
          v-model="selectedFiles"
          :is-uploading="isUploading"
          :error-message="uploadError"
          @submit="submitUpload"
        />
      </SplitterPanel>
      <SplitterPanel :size="45" :min-size="30">
        <ScansList
          :scans="scans"
          :is-loading="isLoadingScans"
          :deleting-case-id="deletingCaseId"
          @delete="handleDeleteScan"
        />
      </SplitterPanel>
    </Splitter>
  </section>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import Message from 'primevue/message'
import Splitter from 'primevue/splitter'
import SplitterPanel from 'primevue/splitterpanel'

import ScansList from '../components/home/ScansList.vue'
import UploadPanel from '../components/home/UploadPanel.vue'
import { deleteScan, fetchScans, subscribeToScans, uploadScan } from '../services/api'

const emptySelectedFiles = () => ({
  t1: null,
  t1ce: null,
  t2: null,
  flair: null,
  true_mask: null
})

const selectedFiles = ref(emptySelectedFiles())
const scans = ref([])
const isLoadingScans = ref(false)
const isUploading = ref(false)
const deletingCaseId = ref('')
const uploadError = ref('')
const pageError = ref('')
let unsubscribeScans = null

async function loadScans() {
  pageError.value = ''
  isLoadingScans.value = true
  try {
    scans.value = await fetchScans()
  } catch {
    pageError.value = 'Could not load scans. Check backend availability.'
  } finally {
    isLoadingScans.value = false
  }
}

async function submitUpload() {
  uploadError.value = ''
  isUploading.value = true

  try {
    const createdScan = await uploadScan(selectedFiles.value)
    scans.value = [createdScan, ...scans.value.filter((scan) => scan.case_id !== createdScan.case_id)]
    selectedFiles.value = emptySelectedFiles()
  } catch {
    uploadError.value = 'Upload failed. Verify file names include modality keywords.'
  } finally {
    isUploading.value = false
  }
}

async function handleDeleteScan(caseId) {
  pageError.value = ''
  deletingCaseId.value = caseId
  try {
    await deleteScan(caseId)
    scans.value = scans.value.filter((scan) => scan.case_id !== caseId)
  } catch {
    pageError.value = `Could not delete scan ${caseId}.`
  } finally {
    deletingCaseId.value = ''
  }
}

onMounted(() => {
  loadScans()
  unsubscribeScans = subscribeToScans((nextScans) => {
    scans.value = nextScans
    pageError.value = ''
  }, () => {
    pageError.value = 'Realtime scan updates are disconnected. The list may be stale.'
  })
})

onUnmounted(() => {
  unsubscribeScans?.()
})
</script>
