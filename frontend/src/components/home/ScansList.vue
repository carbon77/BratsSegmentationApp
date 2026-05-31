<template>
  <Panel :header="t('scansTitle')">
    <Toolbar class="mb-3">
      <template #start>
        <IconField>
          <InputIcon class="pi pi-search" />
          <InputText v-model="searchTerm" :placeholder="t('searchByTitle')" />
        </IconField>
      </template>
      <template #end>
        <Button :label="sortDirection === 'asc' ? t('sortAsc') : t('sortDesc')" :icon="sortDirection === 'asc'
            ? 'pi pi-sort-alpha-down'
            : 'pi pi-sort-alpha-up-alt'
          " outlined @click="toggleSortDirection" />
      </template>
    </Toolbar>

    <ProgressSpinner v-if="isLoading" style="width: 2rem; height: 2rem" strokeWidth="6" />

    <DataTable v-else :value="filteredScans" stripedRows size="small" dataKey="case_id" responsiveLayout="scroll">
      <Column field="title" :header="t('title')">
        <template #body="slotProps">
          <Tag :value="slotProps.data.title || slotProps.data.case_id" />
        </template>
      </Column>
      <Column field="status" :header="t('status')">
        <template #body="slotProps">
          <Tag :value="statusLabel(slotProps.data.status)" :severity="statusSeverity(slotProps.data.status)" />
        </template>
      </Column>
      <Column :header="t('actions')" :style="{ width: '16rem' }">
        <template #body="slotProps">
          <ButtonGroup>
            <RouterLink v-if="slotProps.data.status === 'completed'" :to="`/scans/${slotProps.data.case_id}`">
              <Button size="small" icon="pi pi-external-link" text />
            </RouterLink>
            <Button v-else size="small" icon="pi pi-clock" disabled />
            <Button size="small" icon="pi pi-trash" severity="danger"
              :loading="deletingCaseId === slotProps.data.case_id" @click="$emit('delete', slotProps.data.case_id)" />
          </ButtonGroup>
        </template>
      </Column>
      <template #empty>{{ t("noScans") }}</template>
    </DataTable>
  </Panel>
</template>

<script setup>
import { computed, ref } from "vue";
import { RouterLink } from "vue-router";
import Button from "primevue/button";
import ButtonGroup from "primevue/buttongroup";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import IconField from "primevue/iconfield";
import InputIcon from "primevue/inputicon";
import InputText from "primevue/inputtext";
import Panel from "primevue/panel";
import ProgressSpinner from "primevue/progressspinner";
import Tag from "primevue/tag";
import Toolbar from "primevue/toolbar";

import { usePreferences } from "../../services/preferences";

const props = defineProps({
  scans: {
    type: Array,
    default: () => [],
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
  deletingCaseId: {
    type: String,
    default: "",
  },
});

defineEmits(["delete"]);

const { t } = usePreferences();

const statusLabelKeys = {
  uploading: "statusUploading",
  processing: "statusProcessing",
  completed: "statusCompleted",
  failed: "statusFailed",
  uploaded: "statusUploaded",
};

const statusSeverities = {
  uploading: "info",
  processing: "warn",
  completed: "success",
  failed: "danger",
  uploaded: "info",
};

const searchTerm = ref("");
const sortDirection = ref("asc");

function statusLabel(status) {
  return statusLabelKeys[status] ? t(statusLabelKeys[status]) : status;
}

function statusSeverity(status) {
  return statusSeverities[status] ?? "secondary";
}

function actionUnavailableLabel(status) {
  if (status === "failed") return t("statusFailed");
  return status === "uploading" ? t("statusUploading") : t("statusProcessing");
}

function toggleSortDirection() {
  sortDirection.value = sortDirection.value === "asc" ? "desc" : "asc";
}

const filteredScans = computed(() => {
  const term = searchTerm.value.trim().toLowerCase();
  const scans = term
    ? props.scans.filter((scan) =>
      (scan.title || scan.case_id || "").toLowerCase().includes(term),
    )
    : [...props.scans];

  return scans.sort((first, second) => {
    const firstTitle = (first.title || first.case_id || "").toLowerCase();
    const secondTitle = (second.title || second.case_id || "").toLowerCase();
    const result = firstTitle.localeCompare(secondTitle);
    return sortDirection.value === "asc" ? result : -result;
  });
});
</script>
