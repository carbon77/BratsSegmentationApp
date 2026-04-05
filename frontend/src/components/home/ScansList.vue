<template>
  <Panel header="Created scans" toggleable>
    <ProgressSpinner v-if="isLoading" style="width: 2rem; height: 2rem" strokeWidth="6" />

    <DataTable v-else :value="scans" stripedRows size="small" dataKey="case_id" responsiveLayout="scroll">
      <Column field="case_id" header="Case ID">
        <template #body="slotProps">
          <Tag :value="slotProps.data.case_id" />
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
import { RouterLink } from 'vue-router'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Panel from 'primevue/panel'
import ProgressSpinner from 'primevue/progressspinner'
import Tag from 'primevue/tag'

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
