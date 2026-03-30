<template>
  <section class="space-y-8">
    <Card>
      <template #title>Upload MRI modalities</template>
      <template #content>
        <div class="space-y-4">
          <div
            v-for="modality in modalities"
            :key="modality"
            class="rounded-lg border border-slate-200 p-4"
          >
            <div class="flex items-center justify-between gap-4">
              <div>
                <p class="font-medium uppercase text-slate-700">{{ modality }}</p>
                <p class="text-sm text-slate-500">{{ selectedName(modality) }}</p>
              </div>
              <Button
                :label="selectedFiles[modality] ? 'Replace file' : 'Choose file'"
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
              @click="submitUpload"
            />
            <small class="text-slate-500">All 4 modalities are required.</small>
          </div>

          <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>
        </div>
      </template>
    </Card>

    <Card>
      <template #title>Created scans</template>
      <template #content>
        <div v-if="isLoadingScans" class="py-4">
          <ProgressSpinner style="width: 34px; height: 34px" strokeWidth="6" />
        </div>

        <ul v-else-if="scans.length" class="space-y-2">
          <li
            v-for="scan in scans"
            :key="scan.case_id"
            class="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2"
          >
            <span class="font-mono text-sm">{{ scan.case_id }}</span>
            <RouterLink :to="`/scans/${scan.case_id}`">
              <Button size="small" label="Open" icon="pi pi-arrow-right" iconPos="right" text />
            </RouterLink>
          </li>
        </ul>

        <p v-else class="text-slate-500">No scans yet.</p>
      </template>
    </Card>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'

import { fetchScans, uploadScan } from '../services/api'

const router = useRouter()
const modalities = ['t1', 't1ce', 't2', 'flair']

const inputRefs = reactive({})
const selectedFiles = reactive({
  t1: null,
  t1ce: null,
  t2: null,
  flair: null
})

const scans = ref([])
const isLoadingScans = ref(false)
const isUploading = ref(false)
const errorMessage = ref('')

const allModalitiesSelected = computed(() =>
  modalities.every((modality) => Boolean(selectedFiles[modality]))
)

function setFileInputRef(modality, element) {
  if (element) inputRefs[modality] = element
}

function openPicker(modality) {
  inputRefs[modality]?.click()
}

function onFileSelected(event, modality) {
  const [file] = event.target.files
  selectedFiles[modality] = file ?? null
}

function selectedName(modality) {
  return selectedFiles[modality]?.name ?? 'No file selected'
}

async function loadScans() {
  errorMessage.value = ''
  isLoadingScans.value = true
  try {
    scans.value = await fetchScans()
  } catch {
    errorMessage.value = 'Could not load scans. Check backend availability.'
  } finally {
    isLoadingScans.value = false
  }
}

async function submitUpload() {
  if (!allModalitiesSelected.value) return

  errorMessage.value = ''
  isUploading.value = true

  try {
    const payload = await uploadScan(selectedFiles)
    await loadScans()
    await router.push(`/scans/${payload.case_id}`)
  } catch {
    errorMessage.value = 'Upload failed. Please verify files and try again.'
  } finally {
    isUploading.value = false
  }
}

onMounted(loadScans)
</script>
