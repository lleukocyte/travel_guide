import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// import { createYmaps } from 'vue-yandex-maps'

// const settings = {
//   apiKey: '99aa9b0d-5b50-4ec7-a652-089a0d5ef4ef',
//   lang: 'ru_RU',
//   coordorder: 'latlong',
//   version: '2.1'
// }

const app = createApp(App)
app.use(router)
//app.use(createYmaps(settings))
app.mount('#app')