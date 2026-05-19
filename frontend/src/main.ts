import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router/index.js'

import './assets/styles/reset.css'
import './assets/styles/layout.css'
import './assets/styles/forms.css'
import './assets/styles/tables.css'
import './assets/styles/animations.css'
import 'nprogress/nprogress.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
