<template>
  <Panel :header="t('segmentationSlice')">
    <div class="flex flex-col gap-3">
      <div class="flex flex-col gap-3">
        <InputGroup>
          <InputGroupAddon>{{ t("sliceIndex") }}</InputGroupAddon>
          <InputNumber v-model="localSliceIdx" :min="0" :max="maxSliceIdx" inputId="sliceIdx" />
        </InputGroup>
        <InputGroup>
          <Dropdown id="overlayModality" v-model="overlayModality" :options="overlayOptions" optionLabel="label"
            optionValue="value" :placeholder="t('overlayMaskOnly')" />
          <Button :label="t('loadSlice')" icon="pi pi-image" :loading="isLoading" @click="loadImage" />
          <Button :label="t('downloadPng')" icon="pi pi-download" severity="secondary" :loading="isDownloading"
            :disabled="!imageSrc" outlined @click="downloadImage" />
        </InputGroup>
      </div>

      <Panel :header="t('quickAdjust')">
        <Slider id="sliceSlider" v-model="localSliceIdx" :min="0" :max="maxSliceIdx" />
      </Panel>

      <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>

      <Image v-if="imageSrc" :src="imageSrc" :alt="imageAlt" preview :imageStyle="imageStyle" />
      <Message v-else severity="warn">{{ t("loadSlicePrompt") }}</Message>
    </div>
  </Panel>
</template>

<script setup>
import { computed, onUnmounted, ref, watch } from "vue";
import Button from "primevue/button";
import Dropdown from "primevue/dropdown";
import Image from "primevue/image";
import InputGroup from "primevue/inputgroup";
import InputGroupAddon from "primevue/inputgroupaddon";
import InputNumber from "primevue/inputnumber";
import Message from "primevue/message";
import Panel from "primevue/panel";
import Slider from "primevue/slider";

import { downloadSlice } from "../../services/api";
import { usePreferences } from "../../services/preferences";

const props = defineProps({
  caseId: {
    type: String,
    required: true,
  },
  initialSlice: {
    type: Number,
    default: 60,
  },
});

const { t } = usePreferences();
const maxSliceIdx = 95;
const overlayValues = [null, "t1", "t1ce", "t2", "flair"];
const imageStyle = { width: "100%", maxWidth: "1000px", display: "block" };

const overlayOptions = computed(() =>
  overlayValues.map((value) => ({
    label: value ? `${value.toUpperCase()}` : t("overlayMaskOnly"),
    value,
  })),
);

const localSliceIdx = ref(props.initialSlice);
const overlayModality = ref(null);
const imageSrc = ref("");
const isLoading = ref(false);
const isDownloading = ref(false);
const errorMessage = ref("");

const imageAlt = computed(() => {
  if (!overlayModality.value) return t("maskSliceAlt");
  return t("overlaySliceAlt", {
    modality: overlayModality.value.toUpperCase(),
  });
});

function clearObjectUrl() {
  if (imageSrc.value) {
    URL.revokeObjectURL(imageSrc.value);
    imageSrc.value = "";
  }
}

async function loadImage() {
  isLoading.value = true;
  errorMessage.value = "";

  try {
    const sliceIdx = localSliceIdx.value ?? 0;
    const blob = await downloadSlice(
      props.caseId,
      sliceIdx,
      overlayModality.value,
    );
    clearObjectUrl();
    imageSrc.value = URL.createObjectURL(blob);
  } catch {
    clearObjectUrl();
    errorMessage.value = t("sliceLoadFailed");
  } finally {
    isLoading.value = false;
  }
}

function downloadImage() {
  if (!imageSrc.value) return;

  const overlaySuffix = overlayModality.value
    ? `-${overlayModality.value}-cover`
    : "-mask-only";
  isDownloading.value = true;
  const link = document.createElement("a");
  link.href = imageSrc.value;
  link.download = `${props.caseId}-slice-${localSliceIdx.value ?? 0}${overlaySuffix}.png`;
  link.click();
  isDownloading.value = false;
}

watch([localSliceIdx, overlayModality], () => {
  clearObjectUrl();
  errorMessage.value = "";
});

onUnmounted(clearObjectUrl);
</script>
