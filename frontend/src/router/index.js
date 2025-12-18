import { createRouter, createWebHistory } from 'vue-router'
import Places from '../components/Places.vue'
import Auth from '../components/Auth.vue'
import PlaceDetails from '../components/Place_details.vue'

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
  },
  {
    path: '/place/:id',
    name: 'PlaceDetails',
    component: PlaceDetails
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router