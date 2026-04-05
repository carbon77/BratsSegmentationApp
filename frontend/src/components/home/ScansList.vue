<template>
  <Panel header="Created scans" toggleable>
    <div class="list-toolbar">
      <IconField>
        <InputIcon class="pi pi-search" />
        <InputText v-model="searchTerm" placeholder="Search by title" />
      </IconField>
    </div>

    <ProgressSpinner v-if="isLoading" style="width: 2rem; height: 2rem" strokeWidth="6" />

    <DataTable
      v-else
      :value="filteredScans"
      stripedRows
      size="small"
      dataKey="case_id"
      responsiveLayout="scroll"
    >
      <Column field="title" header="Title">
        <template #body="slotProps">
          <Tag :value="slotProps.data.title || slotProps.data.case_id" />
        </template>
      </Column>
      <Column header="Actions" bodyClass="actions-cell">
        <template #body="slotProps">
          <div class="table-actions">
            <RouterLink :to="`/scans/${slotProps.data.case_id}`">
              <Button size="small" icon="pi pi-external-link" label="Open" text />
            </RouterLink>
            <Button
              size="small"
              label="Delete"
              icon="pi pi-trash"
              severity="danger"
              outlined
              :loading="deletingCaseId === slotProps.data.case_id"
              @click="$emit('delete', slotProps.data.case_id)"
            />
          </div>
        </template>
      </Column>
      <template #empty>No scans yet.</template>
    </DataTable>
  </Panel>
</template>

<script setup>
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'
import Panel from 'primevue/panel'
import ProgressSpinner from 'primevue/progressspinner'
import Tag from 'primevue/tag'

const props = defineProps({
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

const searchTerm = ref('')

const filteredScans = computed(() => {
  const term = searchTerm.value.trim().toLowerCase()
  if (!term) {
    return props.scans
  }

  return props.scans.filter((scan) => (scan.title || '').toLowerCase().includes(term))
})
</script>
