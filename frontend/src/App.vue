<!-- App.vue -->
<template>
  <div id="app">
    <!-- <div v-if="debugInfo" style="background: #f0f0f0; padding: 10px; border-bottom: 1px solid #ccc; font-family: monospace;">
      <strong>Отладка маршрутизатора:</strong><br>
      Путь: <strong>{{ $route.path }}</strong> | 
      Имя маршрута: <strong>{{ $route.name || 'undefined' }}</strong> | 
      Компонент: <strong>{{ currentComponent }}</strong><br>
      Совпавшие маршруты: <strong>{{ matchedRoutes }}</strong>
    </div> -->
    
    <router-view v-if="isRouterReady"></router-view>
    <div v-else style="padding: 20px;">
       Инициализация маршрутизатора...
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'

export default {
  name: 'App',
  setup() {
    const route = useRoute()
    const debugInfo = ref(true)
    const isRouterReady = ref(false)
    
    const currentComponent = computed(() => {
      return route.name || 'Unknown'
    })
    
    const matchedRoutes = computed(() => {
      return route.matched.map(m => m.name).join(', ') || 'none'
    })
    
    watch(route, (newRoute) => {
      console.log('Маршрут изменен:', {
        path: newRoute.path,
        name: newRoute.name,
        matched: newRoute.matched.map(m => m.name)
      })
    }, { immediate: true })
    
    onMounted(() => {
      setTimeout(() => {
        isRouterReady.value = true
        console.log('App.vue mounted, router ready')
      }, 100)
    })
    
    return {
      debugInfo,
      currentComponent,
      matchedRoutes,
      isRouterReady
    }
  }
}
</script>

<style>
#app {
  width: 100%;
  min-height: 100vh;
  font-family: Arial, sans-serif;
}
</style>