<template>
  <div class="auth-container">
    <div class="auth-forms">
      <div class="toggle">
        <button :class="{ active: mode === 'login' }" @click="switchMode('login')">Вход</button>
        <button :class="{ active: mode === 'register' }" @click="switchMode('register')">Регистрация</button>
      </div>

      <form v-if="mode === 'login'" @submit.prevent="login" class="form">
        <div class="form-group">
          <label>Email</label>
          <input type="email" v-model="loginData.email" placeholder="Введите email" required />
        </div>
        <div class="form-group">
          <label>Пароль</label>
          <input type="password" v-model="loginData.password" placeholder="Введите пароль" required />
        </div>
        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? 'Вход...' : 'Войти' }}
        </button>
      </form>

      <form v-else @submit.prevent="register" class="form">
        <div class="form-group">
          <label>Имя пользователя</label>
          <input type="text" v-model="registerData.username" placeholder="Введите имя" required />
        </div>
        <div class="form-group">
          <label>Email</label>
          <input type="email" v-model="registerData.email" placeholder="Введите email" required />
        </div>
        <div class="form-group">
          <label>Пароль</label>
          <input type="password" v-model="registerData.password" placeholder="Не менее 6 символов" required />
        </div>
        <div class="form-group">
          <label>Подтвердите пароль</label>
          <input type="password" v-model="registerData.confirmPassword" placeholder="Повторите пароль" required />
          <div v-if="registerData.confirmPassword && !passwordsMatch" class="error-text">
            Пароли не совпадают
          </div>
        </div>
        <button type="submit" class="submit-btn" :disabled="loading || !isRegisterFormValid">
          {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
        </button>
      </form>

      <p v-if="errorMessage" class="message error">{{ errorMessage }}</p>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

export default {
  name: 'AuthApp',
  setup() {
    const mode = ref('login')
    const errorMessage = ref('')
    const loading = ref(false)
    const router = useRouter()
    
    const API_BASE = 'http://localhost:8000/api'

    const loginData = reactive({ email: '', password: '' })
    const registerData = reactive({ 
      email: '', username: '', password: '', confirmPassword: '' 
    })

    const checkAuth = () => {
      const token = localStorage.getItem('auth_token')
      if (token) {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]))
          const expirationTime = payload.exp * 1000
          const currentTime = Date.now()
          
          if (currentTime < expirationTime) {
            router.push('/catalog')
          }
        } catch (error) {
          // Токен невалиден, остаемся на странице авторизации
          localStorage.removeItem('auth_token')
          localStorage.removeItem('user_data')
        }
      }
    }

    const passwordsMatch = computed(() => 
      registerData.password === registerData.confirmPassword
    )

    const isRegisterFormValid = computed(() => 
      registerData.email && 
      registerData.username && 
      registerData.password && 
      passwordsMatch.value &&
      registerData.password.length >= 6
    )

    const switchMode = (newMode) => {
      mode.value = newMode
      errorMessage.value = ''
    }

    const login = async () => {
      if (loading.value) return
      
      loading.value = true
      errorMessage.value = ''
      
      try {
        const response = await axios.post(`${API_BASE}/login`, loginData)
        const { access_token, username } = response.data
        
        // Сохраняем токен
        localStorage.setItem('auth_token', access_token)
        localStorage.setItem('user_data', JSON.stringify({ username }))
        
        // Переходим в каталог
        router.push('/catalog')
        
        // Очищаем форму
        Object.assign(loginData, { email: '', password: '' })
        
      } catch (error) {
        console.error('Ошибка входа:', error)
        if (error.response?.status === 401 || error.response?.status === 403) {
          errorMessage.value = 'Неверный email или пароль'
        } else {
          errorMessage.value = 'Ошибка входа. Попробуйте позже.'
        }
      } finally {
        loading.value = false
      }
    }

    const register = async () => {
      if (loading.value) return
      
      loading.value = true
      errorMessage.value = ''
      
      try {
        await axios.post(`${API_BASE}/register`, {
          email: registerData.email,
          username: registerData.username,
          password: registerData.password
        })
        
        errorMessage.value = 'Регистрация успешна! Теперь войдите.'
        
        Object.assign(registerData, { 
          email: '', username: '', password: '', confirmPassword: '' 
        })
        mode.value = 'login'
        
      } catch (error) {
        if (error.response?.status === 400) {
          errorMessage.value = error.response.data.detail || 'Ошибка регистрации'
        } else {
          errorMessage.value = 'Ошибка регистрации. Попробуйте позже.'
        }
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      checkAuth()
    })

    return {
      mode,
      errorMessage,
      loginData,
      registerData,
      loading,
      passwordsMatch,
      isRegisterFormValid,
      switchMode,
      login,
      register
    }
  }
}
</script>

<style scoped>
.auth-container {
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
}

.auth-forms {
  max-width: 400px;
  width: 100%;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.toggle {
  display: flex;
  margin-bottom: 20px;
}

.toggle button {
  flex: 1;
  padding: 10px;
  border: none;
  background: none;
  cursor: pointer;
  font-weight: bold;
}

.toggle button.active {
  background: #007bff;
  color: white;
}

.form {
  padding: 20px 0;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.error-text {
  color: #dc3545;
  font-size: 12px;
  margin-top: 5px;
}

.submit-btn {
  width: 100%;
  padding: 10px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.submit-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.message.error {
  color: #dc3545;
  text-align: center;
  margin-top: 15px;
  padding: 10px;
  background: #f8d7da;
  border-radius: 4px;
}
</style>