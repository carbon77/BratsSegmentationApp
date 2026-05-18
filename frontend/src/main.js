import { createApp } from 'vue'
import PrimeVue from 'primevue/config'

import App from './App.vue'
import router from './router'
import { initializePreferences } from './services/preferences'

import 'primevue/resources/themes/lara-light-blue/theme.css'
import 'primevue/resources/primevue.min.css'
import 'primeicons/primeicons.css'
import './style.css'

initializePreferences()

createApp(App)
  .use(router)
  .use(PrimeVue)
  .mount('#app')
