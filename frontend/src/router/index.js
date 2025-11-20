import { createRouter, createWebHistory } from 'vue-router'
import Places from '../components/Places.vue'
import Auth from '../components/Auth.vue'

const routes = [
  {
    path: '/',
    name: 'Auth',
    component: Auth
  },
  {
    path: '/catalog',
    name: 'Catalog',
    component: Places
  },
  {
    path: '/favorites',
    name: 'Favorites',
    component: Places
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  console.log('🔄 Навигация:', from.path, '->', to.path)
  next()
})

router.afterEach((to) => {
  console.log('✅ Переход завершен:', to.path)
  console.log('📍 Активный компонент:', to.name)
})

export default router