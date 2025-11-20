import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(router)

router.isReady().then(() => {
  console.log('🔄 Инициализация маршрутизатора...')
  
  // Если текущий маршрут не активирован, принудительно переходим на '/'
  if (router.currentRoute.value.matched.length === 0) {
    console.log('📍 Принудительная активация корневого маршрута')
    router.replace('/')
  }
  
  app.mount('#app')
}).catch(error => {
  console.error('❌ Ошибка инициализации маршрутизатора:', error)
})