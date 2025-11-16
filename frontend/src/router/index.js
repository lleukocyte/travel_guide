import { createRouter, createWebHistory } from 'vue-router'
import Places from '../components/Places.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    // Главная страница будет обрабатываться в App.vue
    component: { template: '<div></div>' }
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

export default router