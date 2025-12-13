<!-- Auth.vue -->
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
          <input 
            type="password" 
            v-model="registerData.password" 
            placeholder="Не менее 6 символов" 
            required 
          />

          <ul class="password-rules">
            <li :class="{ ok: passwordLengthOk }">
              <span>{{ passwordLengthOk ? "✔" : "✖" }}</span>
              Минимум 6 символов
            </li>
            <li :class="{ ok: passwordLowerOk }">
              <span>{{ passwordLowerOk ? "✔" : "✖" }}</span>
              Есть строчная буква (a–z)
            </li>
            <li :class="{ ok: passwordUpperOk }">
              <span>{{ passwordUpperOk ? "✔" : "✖" }}</span>
              Есть заглавная буква (A–Z)
            </li>
          </ul>
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

      <p v-if="message.text" :class="['message', message.type]">{{ message.text }}</p>
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
    const message = ref({ text: '', type: '' })
    const loading = ref(false)
    const router = useRouter()
    
    const API_BASE = 'http://localhost:8000/api'

    const loginData = reactive({ email: '', password: '' })
    const registerData = reactive({ 
      email: '', username: '', password: '', confirmPassword: '' 
    })

    const passwordLengthOk = computed(() => registerData.password.length >= 6)
    const passwordLowerOk = computed(() => /[a-z]/.test(registerData.password))
    const passwordUpperOk = computed(() => /[A-Z]/.test(registerData.password))

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
          localStorage.removeItem('auth_token')
          localStorage.removeItem('user_data')
        }
      }
    }

    const passwordsMatch = computed(() => 
      registerData.password === registerData.confirmPassword
    )

    const passwordValid = computed(() =>
      passwordLengthOk.value &&
      passwordLowerOk.value &&
      passwordUpperOk.value
    )

    const isRegisterFormValid = computed(() => 
      registerData.email && 
      registerData.username && 
      passwordsMatch.value &&
      passwordValid.value
    )

    const switchMode = (newMode) => {
      mode.value = newMode
      message.value = { text: '', type: '' }
    }

    const login = async () => {
      if (loading.value) return
      
      loading.value = true
      message.value = { text: '', type: '' }
      
      try {
        const response = await axios.post(`${API_BASE}/login`, loginData)
        const { access_token, username } = response.data
        
        localStorage.setItem('auth_token', access_token)
        localStorage.setItem('user_data', JSON.stringify({ username }))
        
        router.push('/catalog')
        
        Object.assign(loginData, { email: '', password: '' })
        
      } catch (error) {
        console.error('Ошибка входа:', error)
        if (error.response?.status === 401 || error.response?.status === 403) {
          message.value = { 
            text: 'Неверный email или пароль', 
            type: 'error' 
          }
        } else {
          message.value = { 
            text: 'Ошибка входа. Попробуйте позже.', 
            type: 'error' 
          }
        }
      } finally {
        loading.value = false
      }
    }

    const register = async () => {
      if (loading.value) return

      if (!passwordValid.value) {
        message.value = { 
          text: "Пароль не соответствует требованиям", 
          type: 'error' 
        }
        loading.value = false
        return
      }
      
      loading.value = true
      message.value = { text: '', type: '' }
      
      try {
        await axios.post(`${API_BASE}/register`, {
          email: registerData.email,
          username: registerData.username,
          password: registerData.password
        })
        
        message.value = { 
          text: 'Регистрация успешна! Теперь войдите.', 
          type: 'success' 
        }
        
        Object.assign(registerData, { 
          email: '', username: '', password: '', confirmPassword: '' 
        })
        
        setTimeout(() => {
          mode.value = 'login'
        }, 2000)
        
      } catch (error) {
        if (error.response?.status === 400) {
          message.value = { 
            text: error.response.data.detail || 'Ошибка регистрации', 
            type: 'error' 
          }
        } else {
          message.value = { 
            text: 'Ошибка регистрации. Попробуйте позже.', 
            type: 'error' 
          }
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
      message,
      loginData,
      registerData,
      loading,
      passwordsMatch,
      isRegisterFormValid,
      passwordLengthOk,
      passwordLowerOk,
      passwordUpperOk,
      passwordValid,
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
  border-bottom: 1px solid #eee;
}

.toggle button {
  flex: 1;
  padding: 12px;
  border: none;
  background: none;
  cursor: pointer;
  font-weight: bold;
  font-size: 16px;
  transition: all 0.3s;
}

.toggle button.active {
  background: #007bff;
  color: white;
  border-radius: 4px;
}

.toggle button:not(.active):hover {
  background: #f0f0f0;
}

.form {
  padding: 20px 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
}

.password-rules {
  list-style: none;
  padding-left: 0;
  margin-top: 8px;
  font-size: 13px;
}

.password-rules li {
  color: #dc3545;
  margin-bottom: 4px;
  display: flex;
  gap: 6px;
  align-items: center;
  transition: color 0.3s;
}

.password-rules li.ok {
  color: #28a745;
}

.password-rules li span {
  font-weight: bold;
  font-size: 12px;
}

.error-text {
  color: #dc3545;
  font-size: 12px;
  margin-top: 5px;
  font-weight: 500;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  transition: background 0.3s;
}

.submit-btn:hover:not(:disabled) {
  background: #0056b3;
}

.submit-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.message {
  margin-top: 20px;
  padding: 12px 16px;
  border-radius: 4px;
  font-weight: 500;
  text-align: center;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.error {
  background-color: #e94253;
  color: rgb(219, 1, 1);
}

.message.success {
  background-color: #34a74f;
  color: rgb(9, 43, 7);
}
</style>