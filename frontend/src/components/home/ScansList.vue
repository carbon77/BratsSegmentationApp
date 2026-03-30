<template>
  <Card class="h-full">
    <template #title>
      <span class="text-emerald-200">Created scans</span>
    </template>
    <template #content>
      <div v-if="isLoading" class="py-4">
        <ProgressSpinner style="width: 34px; height: 34px" strokeWidth="6" />
      </div>

      <ul v-else-if="scans.length" class="space-y-2">
        <li
          v-for="scan in scans"
          :key="scan.case_id"
          class="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-emerald-500/30 bg-slate-800/70 px-3 py-2"
        >
          <span class="font-mono text-sm text-emerald-100">{{ scan.case_id }}</span>
          <div class="flex items-center gap-2">
            <RouterLink :to="`/scans/${scan.case_id}`">
              <Button
                size="small"
                label="Open"
                icon="pi pi-arrow-right"
                iconPos="right"
                class="!border-cyan-400 !text-cyan-200"
                outlined
              />
            </RouterLink>
            <Button
              size="small"
              label="Delete"
              icon="pi pi-trash"
              severity="danger"
              outlined
              :loading="deletingCaseId === scan.case_id"
              @click="$emit('delete', scan.case_id)"
            />
          </div>
        </li>
      </ul>

      <p v-else class="text-slate-300">No scans yet.</p>
    </template>
  </Card>
</template>

<script setup>
import { RouterLink } from 'vue-router'
import Button from 'primevue/button'
import Card from 'primevue/card'
import ProgressSpinner from 'primevue/progressspinner'

defineProps({
  scans: {
    type: Array,
    default: () => []
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  deletingCaseId: {
    type: String,
    default: ''
  }
})

defineEmits(['delete'])
</script>
