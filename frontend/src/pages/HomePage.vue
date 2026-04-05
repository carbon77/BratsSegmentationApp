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
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Message from 'primevue/message'
import Splitter from 'primevue/splitter'
import SplitterPanel from 'primevue/splitterpanel'

import ScansList from '../components/home/ScansList.vue'
import UploadPanel from '../components/home/UploadPanel.vue'
import { deleteScan, fetchScans, uploadScan } from '../services/api'

const router = useRouter()

const selectedFiles = ref({
  t1: null,
  t1ce: null,
  t2: null,
  flair: null,
  true_mask: null
})

const scans = ref([])
const isLoadingScans = ref(false)
const isUploading = ref(false)
const deletingCaseId = ref('')
const uploadError = ref('')
const pageError = ref('')

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
    const payload = await uploadScan(selectedFiles.value)
    await loadScans()
    await router.push(`/scans/${payload.case_id}`)
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

onMounted(loadScans)
</script>
