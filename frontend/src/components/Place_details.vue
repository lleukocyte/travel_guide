<template>
  <div class="place-details">
    <nav class="details-nav">
      <button @click="$router.back()" class="back-btn">← Назад</button>
      <button @click="$router.push('/catalog')" class="nav-btn">Каталог</button>
      <button @click="$router.push('/favorites')" class="nav-btn">Избранное</button>
      <button @click="logout" class="logout-btn">Выйти</button>
    </nav>

    <div v-if="loading" class="loading">Загрузка...</div>
    
    <div v-else-if="place" class="place-content">
      <div class="gallery-section">
        <div class="gallery">
          <div class="main-image">
            <img 
              :src="currentImage" 
              :alt="place.name"
              @error="handleImageError"
            >
          </div>
          <div class="gallery-controls">
            <button 
              @click="prevImage" 
              :disabled="currentImageIndex === 0"
              class="gallery-btn"
            >
              ←
            </button>
            <div class="image-counter">
              {{ currentImageIndex + 1 }} / {{ place.photos.length }}
            </div>
            <button 
              @click="nextImage" 
              :disabled="currentImageIndex === place.photos.length - 1"
              class="gallery-btn"
            >
              →
            </button>
          </div>
          <div class="thumbnails" v-if="place.photos.length > 1">
            <div 
              v-for="(photo, index) in place.photos" 
              :key="index"
              :class="['thumbnail', { active: currentImageIndex === index }]"
              @click="currentImageIndex = index"
            >
              <img :src="getFullImagePath(photo)" :alt="`Фото ${index + 1}`">
            </div>
          </div>
        </div>
      </div>

      <div class="info-section">
        <div class="place-header">
          <h1>{{ place.name }}</h1>
          <button 
            @click="toggleFavorite" 
            :class="['favorite-btn', { active: place.is_favorite }]"
          >
            ❤️
          </button>
        </div>

        <div class="place-meta">
          <div class="rating">
            ⭐ {{ place.average_rating?.toFixed(1) || '0.0' }} 
            <span class="review-count">({{ place.review_count || 0 }} {{ getReviewWord(place.review_count) }})</span>
          </div>
          <div class="location">
            <strong>📍 {{ place.city }}</strong>
            <p>{{ place.address }}</p>
          </div>
          <div class="contacts" v-if="place.contacts">
            <strong>📞 Контакты:</strong>
            <p>{{ place.contacts }}</p>
          </div>
        </div>

        <div class="description">
          <h3>Описание</h3>
          <p>{{ place.description }}</p>
        </div>

        <div class="reviews-section">
          <div class="reviews-header">
            <h2>Отзывы</h2>
            <button 
              @click="showReviewForm = !showReviewForm" 
              class="add-review-btn"
              v-if="isAuthenticated"
            >
              {{ showReviewForm ? 'Отменить' : 'Добавить отзыв' }}
            </button>
          </div>

          <!-- Форма добавления отзыва -->
          <div v-if="showReviewForm && isAuthenticated" class="review-form">
            <h3>Ваш отзыв</h3>
            <form @submit.prevent="submitReview">
              <div class="rating-input">
                <label>Оценка:</label>
                <div class="stars">
                  <span 
                    v-for="star in 5" 
                    :key="star"
                    :class="['star', { active: newReview.rating >= star }]"
                    @click="newReview.rating = star"
                  >
                    ★
                  </span>
                </div>
              </div>
              <div class="form-group">
                <label>Комментарий:</label>
                <textarea 
                  v-model="newReview.comment" 
                  placeholder="Расскажите о вашем опыте..."
                  required
                ></textarea>
              </div>
              <button type="submit" :disabled="addingReview" class="submit-btn">
                {{ addingReview ? 'Отправка...' : 'Опубликовать отзыв' }}
              </button>
            </form>
          </div>

          <!-- Список отзывов -->
          <div class="reviews-list">
            <div 
              v-for="review in reviews" 
              :key="review.id" 
              class="review-item"
            >
              <div class="review-header">
                <div class="reviewer">
                  <strong>{{ review.user_username || 'Аноним' }}</strong>
                  <div class="review-rating">
                    <span class="stars">
                      <span 
                        v-for="star in 5" 
                        :key="star"
                        :class="['star', { active: review.rating >= star }]"
                      >
                        ★
                      </span>
                    </span>
                  </div>
                </div>
                <div class="review-date">
                  {{ formatDate(review.created_at) }}
                </div>
              </div>
              <div class="review-comment">
                {{ review.comment }}
              </div>
            </div>

            <div v-if="reviews.length === 0" class="no-reviews">
              <p>Пока нет отзывов. Будьте первым!</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="error-state">
      <p>Место не найдено</p>
      <button @click="$router.push('/catalog')" class="btn-primary">
        Вернуться в каталог
      </button>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

export default {
  name: 'PlaceDetails',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const placeId = parseInt(route.params.id)
    
    const place = ref(null)
    const loading = ref(true)
    const reviews = ref([])
    const showReviewForm = ref(false)
    const addingReview = ref(false)
    const currentImageIndex = ref(0)

    const BACKEND_BASE = 'http://localhost:8000/'
    const API_BASE = 'http://localhost:8000/api'

    const newReview = reactive({
      rating: 0,
      comment: ''
    })

    const currentImage = computed(() => {
      if (!place.value || !place.value.photos.length) return ''
      return getFullImagePath(place.value.photos[currentImageIndex.value])
    })

    const getFullImagePath = (photoPath) => {
      return BACKEND_BASE + photoPath
    }

    const handleImageError = (event) => {
      console.error('Ошибка загрузки изображения:', event.target.src)
      event.target.src = 'https://via.placeholder.com/600x400/cccccc/969696?text=Изображение+не+загружено'
    }

    const nextImage = () => {
      if (currentImageIndex.value < place.value.photos.length - 1) {
        currentImageIndex.value++
      }
    }

    const prevImage = () => {
      if (currentImageIndex.value > 0) {
        currentImageIndex.value--
      }
    }

    const isAuthenticated = computed(() => {
      return !!localStorage.getItem('auth_token')
    })

    const loadPlace = async () => {
      loading.value = true
      try {
        const token = localStorage.getItem('auth_token')
        const headers = token ? { Authorization: `Bearer ${token}` } : {}
        
        const placeResponse = await axios.get(`${API_BASE}/places/${placeId}`, { headers })
        place.value = placeResponse.data

        const reviewsResponse = await axios.get(`${API_BASE}/places/${placeId}/reviews`)
        reviews.value = reviewsResponse.data
        if (token) {
          try {
            const favResponse = await axios.get(
              `${API_BASE}/favorites/${placeId}/status`,
              { headers }
            )
            place.value.is_favorite = favResponse.data.is_favorite
          } catch (error) {
            place.value.is_favorite = false
          }
        }

      } catch (error) {
        console.error('Ошибка загрузки места:', error)
        place.value = null
      } finally {
        loading.value = false
      }
    }

    const toggleFavorite = async () => {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        alert('Войдите в систему чтобы добавлять в избранное')
        return
      }

      try {
        if (place.value.is_favorite) {
          await axios.delete(`${API_BASE}/favorites/${placeId}`, {
            headers: { Authorization: `Bearer ${token}` }
          })
          place.value.is_favorite = false
        } else {
          await axios.post(`${API_BASE}/favorites/${placeId}`, {}, {
            headers: { Authorization: `Bearer ${token}` }
          })
          place.value.is_favorite = true
        }
      } catch (error) {
        console.error('Ошибка обновления избранного:', error)
      }
    }

    const submitReview = async () => {
      if (!isAuthenticated.value) {
        alert('Войдите в систему чтобы оставлять отзывы')
        return
      }

      if (newReview.rating === 0) {
        alert('Пожалуйста, поставьте оценку')
        return
      }

      if (!newReview.comment.trim()) {
        alert('Пожалуйста, напишите комментарий')
        return
      }

      addingReview.value = true
      try {
        const token = localStorage.getItem('auth_token')
        await axios.post(`${API_BASE}/places/${placeId}/reviews`, {
          rating: newReview.rating,
          comment: newReview.comment.trim(),
          place_id: placeId
        }, {
          headers: { Authorization: `Bearer ${token}` }
        })
      
        newReview.rating = 0
        newReview.comment = ''
        showReviewForm.value = false

        const reviewsResponse = await axios.get(`${API_BASE}/places/${placeId}/reviews`)
        reviews.value = reviewsResponse.data

        const headers = token ? { Authorization: `Bearer ${token}` } : {}
        
        const placeResponse = await axios.get(`${API_BASE}/places/${placeId}`, { headers })
        place.value = placeResponse.data
      
      } catch (error) {
        console.error('Полная ошибка добавления отзыва:', error)

        let errorMessage = 'Неизвестная ошибка при добавлении отзыва'

        if (error.code === 'NETWORK_ERROR') {
          errorMessage = 'Проблемы с соединением. Проверьте подключение.'
        } else if (error.response) {
          const status = error.response.status
          const data = error.response.data

          switch (status) {
            case 400:
              errorMessage = data.detail || 'Неверные данные отзыва'
              break
            case 401:
              errorMessage = 'Необходимо авторизоваться'
              break
            case 404:
              errorMessage = 'Место не найдено'
              break
            case 422:
              errorMessage = 'Ошибка валидации данных'
              break
            default:
              errorMessage = data.detail || `Ошибка сервера (${status})`
          }
        } else if (error.request) {
          errorMessage = 'Сервер не отвечает. Попробуйте позже.'
        } else {
          errorMessage = error.message || 'Неизвестная ошибка'
        }

        alert('Ошибка: ' + errorMessage)
      } finally {
        addingReview.value = false
      }

    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }

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

    const logout = () => {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_data')
      router.push('/')
    }

    onMounted(() => {
      loadPlace()
    })

    return {
      place,
      loading,
      reviews,
      showReviewForm,
      addingReview,
      currentImageIndex,
      currentImage,
      newReview,
      isAuthenticated,
      getFullImagePath,
      handleImageError,
      nextImage,
      prevImage,
      toggleFavorite,
      submitReview,
      formatDate,
      getReviewWord,
      logout
    }
  }
}
</script>

<style scoped>
.place-details {
  min-height: 100vh;
  background: #f5f5f5;
}

.details-nav {
  background: #2c3e50;
  padding: 15px 20px;
  display: flex;
  gap: 15px;
  align-items: center;
}

.back-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.nav-btn {
  color: white;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 4px;
  background: transparent;
  border: 1px solid #34495e;
  cursor: pointer;
}

.logout-btn {
  margin-left: auto;
  background: #e74c3c;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.place-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
}

.gallery-section {
  position: sticky;
  top: 20px;
}

.gallery {
  background: white;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.main-image {
  height: 400px;
  overflow: hidden;
}

.main-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.gallery-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f8f9fa;
}

.gallery-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
}

.gallery-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.image-counter {
  font-weight: bold;
  color: #333;
}

.thumbnails {
  display: flex;
  gap: 10px;
  padding: 15px;
  background: #f8f9fa;
  overflow-x: auto;
}

.thumbnail {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
}

.thumbnail.active {
  border-color: #007bff;
}

.thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.info-section {
  background: white;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.place-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.place-header h1 {
  margin: 0;
  color: #333;
  flex: 1;
  margin-right: 15px;
}

.favorite-btn {
  background: #f8f9fa;
  border: 2px solid #ddd;
  padding: 10px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 18px;
  transition: all 0.3s ease;
}

.favorite-btn.active {
  background: #dc3545;
  border-color: #dc3545;
  color: white;
}

.place-meta {
  margin-bottom: 25px;
}

.rating {
  font-size: 18px;
  color: #f39c12;
  margin-bottom: 15px;
}

.review-count {
  color: #666;
  font-size: 14px;
}

.location, .contacts {
  margin-bottom: 15px;
}

.location strong, .contacts strong {
  color: #333;
}

.description {
  margin-bottom: 30px;
}

.description h3 {
  color: #333;
  margin-bottom: 10px;
}

.reviews-section {
  border-top: 1px solid #eee;
  padding-top: 20px;
}

.reviews-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.add-review-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.review-form {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 25px;
}

.rating-input {
  margin-bottom: 15px;
}

.stars {
  display: flex;
  gap: 5px;
}

.star {
  font-size: 24px;
  color: #ddd;
  cursor: pointer;
  transition: color 0.2s;
}

.star.active {
  color: #f39c12;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  min-height: 100px;
  resize: vertical;
}

.submit-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
}

.submit-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.review-item {
  border-bottom: 1px solid #eee;
  padding: 20px 0;
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.reviewer {
  flex: 1;
}

.review-rating {
  margin-top: 5px;
}

.review-date {
  color: #666;
  font-size: 14px;
}

.review-comment {
  color: #333;
  line-height: 1.5;
}

.no-reviews {
  text-align: center;
  padding: 40px;
  color: #667;
}

.error-state {
  text-align: center;
  padding: 50px 20px;
}

.btn-primary {
  background: #007bff;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
}

.loading {
  text-align: center;
  padding: 50px;
  font-size: 18px;
  color: #666;
}

@media (max-width: 768px) {
  .place-content {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .gallery-section {
    position: static;
  }
  
  .place-header {
    flex-direction: column;
    gap: 15px;
  }
  
  .reviews-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
}
</style>