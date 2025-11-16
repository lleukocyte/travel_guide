<template>
  <div class="places-app">
    <div class="app-container">
      <!-- Боковая панель слева -->
      <aside class="sidebar">
        <nav class="sidebar-nav">
          <ul>
            <li><button @click="selectedTab='catalog'" class="nav-btn">Каталог</button></li>
            <li><button @click="selectedTab='favorites'" class="nav-btn">Избранное</button></li>
          </ul>
        </nav>
        <button @click="logout" class="logout-btn">Выйти</button>
      </aside>

      <!-- Основное содержимое -->
      <main class="main-content">
        <div class="city-selector">
          <label>Город: </label>
          <select v-model="selectedCity" @change="loadPlaces">
            <option value="">Все города</option>
            <option v-for="city in cities" :key="city" :value="city">
              {{ city }}
            </option>
          </select>
          
          <!-- Кнопка добавления места -->
          <button @click="showAddForm = true" class="add-place-btn">
            ➕ Добавить место
          </button>
        </div>

        <div class="content">
          <div v-if="selectedTab==='catalog'">
            <!-- Загрузка -->
            <div v-if="loading" class="loading">Загрузка мест...</div>
            
            <!-- Сетка мест -->
            <div v-else class="places-grid">
              <div v-for="place in places" :key="place.id" class="place-card">
                <div class="place-image">
                  <img v-if="place.photos && place.photos.length > 0" :src="place.photos[0]" :alt="place.name">
                  <div v-else class="no-image">📷</div>
                </div>
                <div class="place-content">
                  <h3>{{ place.name }}</h3>
                  <p class="place-city">{{ place.city }}</p>
                  <p class="place-address">{{ place.address }}</p>
                  <p class="place-description">{{ place.description }}</p>
                  <div class="place-rating">
                    ⭐ {{ place.average_rating?.toFixed(1) || '0.0' }} 
                    <span class="review-count">({{ place.review_count || 0 }} отзывов)</span>
                  </div>
                  <div class="place-actions">
                    <button @click="viewPlaceDetails(place)" class="btn-details">
                      Подробнее
                    </button>
                    <button 
                      @click="toggleFavorite(place)" 
                      :class="['btn-favorite', { active: place.is_favorite }]"
                    >
                      ❤️
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Состояние пустого списка -->
            <div v-if="!loading && places.length === 0" class="empty-state">
              <p>В выбранном городе пока нет мест</p>
              <button @click="showAddForm = true" class="btn-primary">
                Добавить первое место
              </button>
            </div>
          </div>
          <div v-else-if="selectedTab==='favorites'">
            <!-- сетка избранного -->
            <PlacesFavorites />
          </div>
        </div>
      </main>
    </div>

     <!-- Модальное окно добавления места -->
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
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'PlacesApp',
  setup() {
    const selectedCity = ref('')
    const loading = ref(false)
    const cities = ref([])
    const places = ref([])
    const showAddForm = ref(false)
    const addingPlace = ref(false)
    const selectedTab = ref('catalog')
    const fileInput = ref(null)

    const newPlace = reactive({
      name: '',
      city: '',
      address: '',
      contacts: '',
      description: '',
      photoFiles: [],
      photoError: ''
    })

    const API_BASE = 'http://localhost:8000'

    const handlePhotoUpload = (event) => {
      const files = Array.from(event.target.files)
      
      // Проверяем количество файлов
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


    const loadCities = async () => {
      try { 
        const response = await axios.get(`${API_BASE}/places/cities`)
        cities.value = response.data.cities
      } catch (error) { 
        console.error('Ошибка загрузки городов:', error)
      }
    }

    // Загрузка мест
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
        
        // Проверяем статус избранного для каждого места
        if (token) {
          for (let place of places.value) {
            try {
              const favResponse = await axios.get(
                `${API_BASE}/places/${place.id}/favorites/status`,
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

    // Добавление нового места
    const addNewPlace = async () => {
      if (addingPlace.value) return
      addingPlace.value = true

      try {
        const token = localStorage.getItem('auth_token')
        if (!token) {
          alert('Необходимо войти в систему')
          return
        }

        // Проверяем, что загружены фото
        if (newPlace.photoFiles.length === 0) {
          newPlace.photoError = 'Необходимо загрузить хотя бы одну фотографию'
          return
        }

        // Создаем FormData
        const formData = new FormData()
        formData.append('name', newPlace.name)
        formData.append('city', newPlace.city)
        formData.append('address', newPlace.address)
        formData.append('contacts', newPlace.contacts)
        formData.append('description', newPlace.description)
        
        // Добавляем каждый файл
        newPlace.photoFiles.forEach(file => {
          formData.append('photos', file)
        })

        console.log('Отправка данных...')
        
        await axios.post(`${API_BASE}/places`, formData, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        })

        // Закрываем форму и сбрасываем данные
        showAddForm.value = false
        resetNewPlaceForm()
        
        // Перезагружаем список мест
        await loadPlaces()
        
        alert('Место успешно добавлено!')

      } catch (error) {
        console.error('Ошибка добавления места:', error)
        alert('Ошибка при добавлении места: ' + (error.response?.data?.detail || error.message))
      } finally {
        addingPlace.value = false
      }
    }

    // Функция сброса формы
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

    // Отмена добавления
    const cancelAddPlace = () => {
      showAddForm.value = false
      resetNewPlaceForm()
    }

    // Просмотр деталей места
    const viewPlaceDetails = (place) => {
      console.log('Просмотр места:', place)
      // Здесь можно добавить переход на страницу деталей
      alert(`Детали места: ${place.name}\nАдрес: ${place.address}\nРейтинг: ${place.average_rating}`)
    }

    // Добавление/удаление из избранного
    const toggleFavorite = async (place) => {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        alert('Войдите в систему чтобы добавлять в избранное')
        return
      }

      try {
        if (place.is_favorite) {
          await axios.delete(`${API_BASE}/places/${place.id}/favorites`, {
            headers: { Authorization: `Bearer ${token}` }
          })
          place.is_favorite = false
        } else {
          await axios.post(`${API_BASE}/places/${place.id}/favorites`, {}, {
            headers: { Authorization: `Bearer ${token}` }
          })
          place.is_favorite = true
        }
      } catch (error) {
        console.error('Ошибка обновления избранного:', error)
      }
    }

    // Выход из системы
    const logout = () => {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_data')
      window.location.reload() // Перезагружаем страницу для возврата к форме входа
    }

    // Загружаем данные при монтировании компонента
    onMounted(() => {
      loadCities()
      loadPlaces()
    })

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
      loadPlaces,
      addNewPlace,
      handlePhotoUpload,
      cancelAddPlace,
      viewPlaceDetails,
      toggleFavorite,
      logout
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

/* Боковая панель */
.sidebar {
  width: 250px;
  background: #2c3e50;
  padding: 20px;
  display: flex;
  flex-direction: column;
  color: white;
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
  margin-top: auto;
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

/* Основное содержимое */
.main-content {
  flex: 1;
  padding: 20px;
  background: white;
  margin: 20px;
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

/* Стили для модального окна */
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

@media (max-width: 768px) {
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