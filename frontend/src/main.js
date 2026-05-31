import { createApp } from 'vue'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'

import App from './App.vue'
import router from './router'
import "./style.css"
import { initializePreferences } from './services/preferences'

import 'primevue/resources/primevue.min.css'
import 'primeicons/primeicons.css'

initializePreferences()

createApp(App)
  .use(router)
  .use(PrimeVue, {
    theme: {
      preset: Aura,
    }
  })
  .mount('#app')
