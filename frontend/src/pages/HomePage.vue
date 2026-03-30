<template>
  <section class="space-y-4">
    <Message v-if="pageError" severity="error">{{ pageError }}</Message>

    <div class="grid gap-6 lg:grid-cols-2">
      <UploadPanel
        v-model="selectedFiles"
        :is-uploading="isUploading"
        :error-message="uploadError"
        @submit="submitUpload"
      />
      <ScansList :scans="scans" :is-loading="isLoadingScans" />
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Message from 'primevue/message'

import ScansList from '../components/home/ScansList.vue'
import UploadPanel from '../components/home/UploadPanel.vue'
import { fetchScans, uploadScan } from '../services/api'

const router = useRouter()

const selectedFiles = ref({
  t1: null,
  t1ce: null,
  t2: null,
  flair: null
})

const scans = ref([])
const isLoadingScans = ref(false)
const isUploading = ref(false)
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

onMounted(loadScans)
</script>
