<template>
  <div class="places-app">
    <div class="app-container">
      <aside class="sidebar">
        <nav class="sidebar-nav">
          <ul>
            <button @click="navigateTo('catalog')" class="nav-btn">Каталог</button>
            <button @click="navigateTo('favorites')" class="nav-btn">Избранное</button>
          </ul>
        </nav>
        <button @click="logout" class="logout-btn">Выйти</button>
      </aside>

      <main class="main-content">
        <div class="city-selector">
          <label>Город: </label>
          <select v-model="selectedCity" @change="onCityChange">
            <option value="">Все города</option>
            <option v-for="city in cities" :key="city" :value="city">
              {{ city }}
            </option>
          </select>
        </div>

        <!-- Карта -->
        <div v-show="selectedCity && !loading && filteredPlaces.length > 0" class="map-section">
          <div id="yandex-map" ref="mapContainer" class="map-container"></div>
        </div>

        <div class="content">
          <div v-if="selectedTab==='catalog'">
            <div class="catalog-header">
              <button @click="showAddForm = true" class="add-place-btn">
                ➕ Добавить место
              </button>
            </div>
            <div v-if="loading" class="loading">Загрузка мест...</div>
            
            <div v-else class="places-grid">
              <div v-for="place in places" :key="place.id" class="place-card">
                <div class="place-image" @click="viewPlaceDetails(place)">
                  <img v-if="place.photos && place.photos.length > 0" :src="getImageUrl(place.photos[0])" :alt="place.name" @error="handleImageError">
                  <div v-else class="no-image">📷</div>
                </div>
                <div class="place-content">
                  <h3 @click="viewPlaceDetails(place)" class="clickable-title">{{ place.name }}</h3>
                  <p class="place-city">{{ place.city }}</p>
                  <p class="place-address">{{ place.address }}</p>
                  <div class="place-rating">
                    ⭐ {{ place.average_rating?.toFixed(1) || '0.0' }}
                    <span class="review-count">({{ place.review_count || 0 }} {{ getReviewWord(place.review_count) }})</span>
                  </div>
                  <div class="place-actions">
                    <button 
                      @click.stop="toggleFavorite(place)" 
                      :class="['btn-favorite', { active: place.is_favorite }]"
                    >
                      {{ place.is_favorite ? '❤️' : '🤍' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="!loading && places.length === 0" class="empty-state">
              <p>В выбранном городе пока нет мест</p>
              <button @click="showAddForm = true" class="btn-primary">
                Добавить первое место
              </button>
            </div>
          </div>

          <div v-else-if="selectedTab==='favorites'">
            <div v-if="loading" class="loading">Загрузка избранного...</div>

            <div v-else class="places-grid">
              <div v-for="favorite in userFavorites" :key="favorite.id" class="place-card">
                <div class="place-image" @click="viewPlaceDetails(favorite)">
                  <img v-if="favorite.photos && favorite.photos.length > 0" 
                       :src="getImageUrl(favorite.photos[0])" 
                       :alt="favorite.name"
                       @error="handleImageError">
                  <div v-else class="no-image">📷</div>
                </div>
                <div class="place-content">
                  <h3 @click="viewPlaceDetails(favorite)" class="clickable-title">{{ favorite.name }}</h3>
                  <p class="place-city">{{ favorite.city }}</p>
                  <p class="place-address">{{ favorite.address }}</p>
                  <div class="place-rating">
                    ⭐ {{ favorite.average_rating?.toFixed(1) || '0.0' }} 
                    <span class="review-count">({{ favorite.review_count || 0 }} {{ getReviewWord(favorite.review_count) }})</span>
                  </div>
                  <div class="place-actions">
                    <button 
                      @click.stop="toggleFavorite(favorite)" 
                      :class="['btn-favorite', { active: true }]"
                    >
                      ❤️
                    </button>
                  </div>
                </div>
              </div>
            </div>
          
            <div v-if="!loading && userFavorites.length === 0" class="empty-state">
              <p>В избранном пока нет мест</p>
            </div>
          </div>
        </div>
      </main>
    </div>

    <div v-if="showAddForm" class="modal-overlay">
      <div class="modal-content">
        <h2>Добавить новое место</h2>
        <form @submit.prevent="addNewPlace" class="add-place-form" enctype="multipart/form-data">
          <div class="form-group">
            <label>Название места *</label>
            <input v-model="newPlace.name" type="text" required>
          </div>
          
          <div class="form-group">
            <label>Город *</label>
            <input v-model="newPlace.city" type="text" required>
          </div>
          
          <div class="form-group">
            <label>Адрес *</label>
            <input v-model="newPlace.address" type="text" required>
          </div>
          
          <div class="form-group">
            <label>Контакты *</label>
            <input v-model="newPlace.contacts" type="text" required>
          </div>
          
          <div class="form-group">
            <label>Описание *</label>
            <textarea v-model="newPlace.description" required></textarea>
          </div>
          
          <div class="form-group">
            <label>Фотографии (до 3 штук, PNG/JPG)</label>
            <input 
              type="file" 
              @change="handlePhotoUpload" 
              accept=".png,.jpg,.jpeg" 
              multiple
              ref="fileInput"
            >
            <div class="file-info" v-if="newPlace.photoFiles.length > 0">
              Выбрано файлов: {{ newPlace.photoFiles.length }}
            </div>
            <div v-if="newPlace.photoError" class="error-text">{{ newPlace.photoError }}</div>
          </div>
          
          <div class="form-actions">
            <button type="button" @click="cancelAddPlace" class="btn-cancel">
              Отмена
            </button>
            <button type="submit" class="btn-primary" :disabled="addingPlace">
              {{ addingPlace ? 'Добавление...' : 'Добавить место' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted, nextTick, computed} from 'vue'
import axios from 'axios'
import { useRoute, useRouter } from 'vue-router'

export default {
  name: 'PlacesApp',
  setup() {
    let map = null;
    let mapContainer = ref(null);
    let mapInitialized = ref(false);
    const selectedCity = ref('')
    const loading = ref(false)
    const cities = ref([])
    const places = ref([])
    const showAddForm = ref(false)
    const addingPlace = ref(false)
    const fileInput = ref(null)
    const userFavorites = ref([])
    
    const route = useRoute()
    const router = useRouter()

    const selectedTab = computed(() => {
      return route.name === 'Favorites' ? 'favorites' : 'catalog'
    })

    const newPlace = reactive({
      name: '',
      city: '',
      address: '',
      contacts: '',
      description: '',
      photoFiles: [],
      photoError: ''
    })

    const API_BASE = 'http://localhost:8000/api'
    const BACKEND_BASE = 'http://localhost:8000'

    const filteredPlaces = computed(() => {
      if (!selectedCity.value) return []
      return places.value.filter(place => place.city === selectedCity.value)
    })

    const loadMap = () => {
      return new Promise((resolve) => {
        if (window.ymaps) {
          resolve(window.ymaps);
          return;
        }
      });
    };

    const initMap = async () => {
      if (!selectedCity.value) return
      
      const ymaps = await loadMap();
      if (!ymaps || !mapContainer.value) return
      
      try {
        const geocodeResult = await ymaps.geocode(selectedCity.value, { results: 1 });
        const firstGeoObject = geocodeResult.geoObjects.get(0);
        let center = [55.751244, 37.618423];
        
        if (firstGeoObject) {
          center = firstGeoObject.geometry.getCoordinates();
        }
        
        map = new ymaps.Map(mapContainer.value, {
          center: center,
          zoom: 12,
          controls: ['zoomControl', 'typeSelector', 'fullscreenControl']
        });
        
        const placesWithCoords = filteredPlaces.value.filter(place => {
          const hasCoords = place.latitude && place.longitude && 
                          !isNaN(parseFloat(place.latitude)) && 
                          !isNaN(parseFloat(place.longitude))          
          return hasCoords
        });
        
        console.log(`Всего мест: ${filteredPlaces.value.length}, с координатами: ${placesWithCoords.length}`)
        
        // Добавляем метки только для мест с координатами
        placesWithCoords.forEach(place => {
          const coords = [parseFloat(place.latitude), parseFloat(place.longitude)];
          
          const placemark = new ymaps.Placemark(coords, {
            hintContent: `
              <div class="map-hint">
                <strong>${place.name}</strong>
                <br>⭐ ${place.average_rating?.toFixed(1) || '0.0'}
                <br>${place.address}
              </div>
            `,
            balloonContent: `
              <div class="map-balloon">
                <div class="balloon-header">
                  <h4>${place.name}</h4>
                  <div class="rating">⭐ ${place.average_rating?.toFixed(1) || '0.0'}</div>
                </div>
                <div class="balloon-content">
                  ${place.photos && place.photos.length > 0 
                    ? `<img src="${getImageUrl(place.photos[0])}" alt="${place.name}" class="balloon-photo" onerror="this.style.display='none'">`
                    : '<div class="no-photo">📷 Нет фото</div>'
                  }
                  <div class="balloon-info">
                    <p><strong>Адрес:</strong> ${place.address}</p>
                    <p><strong>Город:</strong> ${place.city}</p>
                    <p><strong>Координаты:</strong> ${place.latitude.toFixed(6)}, ${place.longitude.toFixed(6)}</p>
                  </div>
                </div>
              </div>
            `
          }, {
            preset: 'islands#blueIcon'
          });
          
          placemark.events.add('click', () => {
            viewPlaceDetails(place);
          });
          
          map.geoObjects.add(placemark);
        });
        
        mapInitialized.value = true;
        
      } catch (error) {
        console.error('Ошибка инициализации карты:', error);
      }
    };

    // Вспомогательные функции
    const getReviewWord = (count) => {
      if (!count) return 'отзывов'
      
      const lastDigit = count % 10
      const lastTwoDigits = count % 100
      
      if (lastTwoDigits >= 11 && lastTwoDigits <= 14) {
        return 'отзывов'
      }
      
      if (lastDigit === 1) {
        return 'отзыв'
      }
      
      if (lastDigit >= 2 && lastDigit <= 4) {
        return 'отзыва'
      }
      
      return 'отзывов'
    }

    const getImageUrl = (photoPath) => {
      if (!photoPath) return ''
      return photoPath.startsWith('http') ? photoPath : `${BACKEND_BASE}/${photoPath}`
    }

    const handleImageError = (event) => {
      event.target.src = 'https://via.placeholder.com/300x200/cccccc/969696?text=Изображение+не+загружено'
    }

    // Функции загрузки данных
    const loadCities = async () => {
      try { 
        const response = await axios.get(`${API_BASE}/places/cities`)
        cities.value = response.data.cities
      } catch (error) { 
        console.error('Ошибка загрузки городов:', error)
      }
    }

    const loadPlaces = async () => {
      loading.value = true
      try {
        const token = localStorage.getItem('auth_token')
        const params = selectedCity.value ? { city: selectedCity.value } : {}
        
        const response = await axios.get(`${API_BASE}/places`, {
          params,
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        })
        
        places.value = response.data
        
        if (token) {
          for (let place of places.value) {
            try {
              const favResponse = await axios.get(
                `${API_BASE}/favorites/${place.id}/status`,
                { headers: { Authorization: `Bearer ${token}` } }
              )
              place.is_favorite = favResponse.data.is_favorite
            } catch (error) {
              place.is_favorite = false
            }
          }
        }
      } catch (error) {
        console.error('Ошибка загрузки мест:', error)
      } finally {
        loading.value = false
      }
    }

    const addNewPlace = async () => {
      if (addingPlace.value) return
      addingPlace.value = true

      try {
        const token = localStorage.getItem('auth_token')
        if (!token) {
          alert('Необходимо войти в систему')
          return
        }

        if (newPlace.photoFiles.length === 0) {
          newPlace.photoError = 'Необходимо загрузить хотя бы одну фотографию'
          return
        }

        const formData = new FormData()
        formData.append('name', newPlace.name)
        formData.append('city', newPlace.city)
        formData.append('address', newPlace.address)
        formData.append('contacts', newPlace.contacts)
        formData.append('description', newPlace.description)
        
        newPlace.photoFiles.forEach(file => {
          formData.append('photos', file)
        })

        await axios.post(`${API_BASE}/places`, formData, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        })

        showAddForm.value = false
        
        resetNewPlaceForm()
        
        await loadPlaces()
        await loadCities()

      } catch (error) {
        console.error('Ошибка добавления места:', error)
        alert('Ошибка при добавлении места: ' + (error.response?.data?.detail || error.message))
      } finally {
        addingPlace.value = false
      }
    }

    const handlePhotoUpload = (event) => {
      const files = Array.from(event.target.files)
      
      if (files.length > 3) {
        newPlace.photoError = 'Можно загрузить не более 3 фотографий'
        newPlace.photoFiles = []
        if (fileInput.value) {
          fileInput.value.value = ''
        }
        return
      }
      
      const invalidFiles = files.filter(file => {
        const validTypes = ['image/png', 'image/jpeg', 'image/jpg']
        return !validTypes.includes(file.type)
      })
      
      if (invalidFiles.length > 0) {
        newPlace.photoError = 'Допустимые форматы: PNG или JPG'
        newPlace.photoFiles = []
        if (fileInput.value) {
          fileInput.value.value = ''
        }
        return
      }
      
      newPlace.photoError = ''
      newPlace.photoFiles = files
    }

    const resetNewPlaceForm = () => {
      newPlace.name = ''
      newPlace.city = ''
      newPlace.address = ''
      newPlace.contacts = ''
      newPlace.description = ''
      newPlace.photoFiles = []
      newPlace.photoError = ''
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }

    const viewPlaceDetails = (place) => {
      router.push(`/place/${place.id}`)
    }

    const toggleFavorite = async (place) => {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        alert('Войдите в систему чтобы добавлять в избранное')
        return
      }
    
      try {
        if (selectedTab.value === 'favorites') {
          await axios.delete(`${API_BASE}/favorites/${place.id}`, {
            headers: { Authorization: `Bearer ${token}` }
          })
          await loadFavorites()
          return
        } else if (place.is_favorite) {
          await axios.delete(`${API_BASE}/favorites/${place.id}`, {
            headers: { Authorization: `Bearer ${token}` }
          })
          place.is_favorite = false
        } else {
          await axios.post(`${API_BASE}/favorites/${place.id}`, {}, {
            headers: { Authorization: `Bearer ${token}` }
          })
          place.is_favorite = true
        }

      } catch (error) {
        let errorMessage = 'Неизвестная ошибка'
        if (error.response?.data?.detail) {
          errorMessage = error.response.data.detail
        } else if (error.response?.data) {
          errorMessage = JSON.stringify(error.response.data)
        } else if (error.message) {
          errorMessage = error.message
        }

        alert('Ошибка при обновлении избранного: ' + errorMessage)
      }
    }

    const loadFavorites = async () => {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        userFavorites.value = []
        return
      }

      loading.value = true
      try {
        const response = await axios.get(`${API_BASE}/favorites`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        userFavorites.value = response.data
      } catch (error) {
        console.error('Ошибка загрузки избранного:', error)
        userFavorites.value = []
      } finally {
        loading.value = false
      }
    }

    const navigateTo = (tab) => {
      if (tab === 'favorites') {
        router.push('/favorites')
        loadFavorites()
      } else {
        router.push('/catalog')
      }
    }

    const cancelAddPlace = () => {
      showAddForm.value = false
      resetNewPlaceForm()
    }

    const logout = () => {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_data')
      window.location.href = '/'
    }
    
    // Методы для работы с картой
    const getPlaceHint = (place) => {
      return `
        <div class="map-hint">
          <strong>${place.name}</strong>
          <br>⭐ ${place.average_rating?.toFixed(1) || '0.0'}
        </div>
      `
    }
    
    const getPlaceBalloon = (place) => {
      const photo = place.photos && place.photos.length > 0 
        ? `<img src="${getImageUrl(place.photos[0])}" alt="${place.name}" class="balloon-photo" onerror="this.style.display='none'">`
        : '<div class="no-photo">📷 Нет фото</div>'
      
      return `
        <div class="map-balloon">
          <div class="balloon-header">
            <h4>${place.name}</h4>
            <div class="rating">⭐ ${place.average_rating?.toFixed(1) || '0.0'}</div>
          </div>
          <div class="balloon-content">
            ${photo}
            <div class="balloon-info">
              <p><strong>Адрес:</strong> ${place.address}</p>
              <p><strong>Город:</strong> ${place.city}</p>
              <p><strong>Отзывы:</strong> ${place.review_count || 0}</p>
            </div>
          </div>
          <div class="balloon-actions">
            <button class="balloon-btn" data-place-id="${place.id}">
              Подробнее
            </button>
          </div>
        </div>
      `
    }
    
    const onMapClick = (e) => {
      console.log('Координаты клика:', e.get('coords'))
    }
    
    const onMarkerClick = (place) => {
      viewPlaceDetails(place)
    }
    
    const setupBalloonHandlers = () => {
      document.addEventListener('click', (e) => {
        if (e.target.classList.contains('balloon-btn')) {
          const placeId = parseInt(e.target.getAttribute('data-place-id'))
          const place = places.value.find(p => p.id === placeId)
          if (place) {
            viewPlaceDetails(place)
          }
        }
      })
    }

    const destroyMap = () => {
      if (map) {
        map.destroy()
        map = null
        mapInitialized.value = false
      }
    }
    
    const onCityChange = async () => {
        destroyMap()
        await loadPlaces()
        await nextTick()
        await initMap()
    }

    onMounted(() => {
      setupBalloonHandlers()
      loadCities()
      loadPlaces()
      loadFavorites()
      
      const checkYmaps = () => {
        if (typeof window.ymaps !== 'undefined') {
          console.log('API Яндекс.Карт загружено, готово к геокодированию')
        } else {
          setTimeout(checkYmaps, 100)
        }
      }
      checkYmaps()
    })

    onUnmounted(() => {
      if (map) {
        map.destroy();
      }
      window.removeEventListener('viewPlace', () => {});
    });

    return {
      selectedCity,
      cities,
      places,
      loading,
      showAddForm,
      addingPlace,
      newPlace,
      selectedTab,
      fileInput,
      userFavorites,
      mapContainer,
      filteredPlaces,
      getReviewWord,
      getImageUrl,
      handleImageError,
      loadPlaces,
      addNewPlace,
      handlePhotoUpload,
      viewPlaceDetails,
      toggleFavorite,
      cancelAddPlace,
      loadFavorites,
      navigateTo,
      logout,
      destroyMap,
      onCityChange,
      getPlaceHint,
      getPlaceBalloon,
      onMapClick,
      onMarkerClick
    }
  }
}
</script>

<style scoped>
.places-app {
  min-height: 100vh;
  background: #f5f5f5;
}

.app-container {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 250px;
  min-height: 100vh;
  height: auto;
  background: #2c3e50;
  padding: 20px;
  display: flex;
  flex-direction: column;
  color: white;
  justify-content: space-between;
}

.sidebar-nav ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.sidebar-nav li {
  margin-bottom: 10px;
}

.nav-btn {
  width: 100%;
  padding: 12px 16px;
  background: transparent;
  border: 1px solid #34495e;
  color: white;
  border-radius: 6px;
  cursor: pointer;
  text-align: left;
  transition: all 0.3s ease;
}

.nav-btn:hover {
  background: #34495e;
  border-color: #4a6572;
}

.logout-btn {
  margin-bottom: 20px;
  background: #e74c3c;
  color: white;
  border: none;
  padding: 12px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  transition: background 0.3s ease;
}

.logout-btn:hover {
  background: #c0392b;
}

.main-content {
  flex: 1;
  padding: 20px;
  background: white;
  margin: 20px 20px 20px 270px;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.city-selector {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.city-selector label {
  font-weight: bold;
  margin-right: 10px;
}

.city-selector select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 5px;
  margin-right: auto;
}

.catalog-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
  padding: 0 20px;
}

.add-place-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
  transition: background 0.3s ease;
}

.add-place-btn:hover {
  background: #218838;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
  font-size: 18px;
}

.places-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 25px;
}

.place-card {
  background: white;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.place-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

.place-image {
  height: 200px;
  background: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.place-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.no-image {
  font-size: 48px;
  color: #ccc;
}

.place-content {
  padding: 20px;
}

.place-content h3 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 1.3em;
}

.place-city {
  color: #007bff;
  font-weight: bold;
  margin: 0 0 5px 0;
  font-size: 0.9em;
}

.place-address {
  color: #666;
  margin: 0 0 10px 0;
  font-size: 0.9em;
}

.place-description {
  color: #888;
  margin: 0 0 15px 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.place-rating {
  color: #f39c12;
  font-weight: bold;
  margin-bottom: 15px;
}

.review-count {
  color: #666;
  font-weight: normal;
  font-size: 0.9em;
}

.place-actions {
  display: flex;
  gap: 10px;
}

.btn-details {
  flex: 1;
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 5px;
  cursor: pointer;
  transition: background 0.3s ease;
}

.btn-details:hover {
  background: #0056b3;
}

.clickable-area {
  cursor: pointer;
  transition: all 0.2s ease;
}

.clickable-area:hover {
  opacity: 0.8;
}

.place-card {
  cursor: default;
}

.btn-favorite {
  background: #f8f9fa;
  border: 1px solid #ddd;
  padding: 8px 12px;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-favorite.active {
  background: #dc3545;
  color: white;
  border-color: #dc3545;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.empty-state p {
  color: #666;
  margin-bottom: 20px;
  font-size: 1.1em;
}

.btn-primary {
  background: #007bff;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
  transition: background 0.3s ease;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-primary:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 10px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-content h2 {
  margin: 0 0 20px 0;
  color: #333;
}

.add-place-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-weight: bold;
  margin-bottom: 5px;
  color: #333;
}

.form-group input,
.form-group textarea {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 14px;
}

.form-group textarea {
  height: 100px;
  resize: vertical;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.btn-cancel {
  background: #6c757d;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  transition: background 0.3s ease;
}

.btn-cancel:hover {
  background: #5a6268;
}

.map-section {
  margin-bottom: 30px;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.map-container {
  height: 400px;
  background: #f8f9fa;
}

.map-hint {
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.2);
  font-size: 14px;
  max-width: 200px;
}

.map-balloon {
  padding: 15px;
  max-width: 300px;
}

.balloon-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.balloon-header h4 {
  margin: 0;
  color: #333;
  flex: 1;
  margin-right: 10px;
}

.balloon-header .rating {
  color: #f39c12;
  font-weight: bold;
  white-space: nowrap;
}

.balloon-content {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
}

.balloon-photo {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 6px;
}

.no-photo {
  width: 80px;
  height: 80px;
  background: #f8f9fa;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

.balloon-info {
  flex: 1;
}

.balloon-info p {
  margin: 5px 0;
  font-size: 13px;
  color: #555;
}

.balloon-info strong {
  color: #333;
}

.balloon-actions {
  text-align: center;
}

.balloon-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.3s ease;
}

.balloon-btn:hover {
  background: #0056b3;
} 

@media (max-width: 768px) {
  .balloon-content {
    flex-direction: column;
  }
  
  .balloon-photo,
  .no-photo {
    width: 100%;
    height: 120px;
  }
  
  .map-container {
    height: 300px;
  }

  .app-container {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    flex-direction: row;
    justify-content: space-between;
    padding: 10px;
  }
  
  .sidebar-nav ul {
    display: flex;
    gap: 10px;
  }
  
  .logout-btn {
    margin-top: 0;
  }
  
  .main-content {
    margin: 10px;
    padding: 15px;
  }
  
  .city-selector {
    flex-direction: column;
    gap: 15px;
  }
  
  .places-grid {
    grid-template-columns: 1fr;
  }
  
  .modal-content {
    margin: 20px;
    width: calc(100% - 40px);
  }

  .file-info {
    margin-top: 5px;
    color: #666;
    font-size: 0.9em;
  }

  .error-text {
    color: #dc3545;
    font-size: 0.9em;
    margin-top: 5px;
  }
}
</style>