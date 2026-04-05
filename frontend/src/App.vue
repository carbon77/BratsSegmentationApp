<template>
  <div class="app-shell">
    <Toolbar class="app-toolbar">
      <template #start>
        <RouterLink to="/" class="brand-link">Brats Segmentation App</RouterLink>
      </template>
      <template #end>
        <Tag value="PrimeVue Workspace" severity="info" rounded />
      </template>
    </Toolbar>

    <main class="page-content">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { RouterLink, RouterView } from 'vue-router'
import Tag from 'primevue/tag'
import Toolbar from 'primevue/toolbar'
</script>
