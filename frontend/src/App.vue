<template>
  <div class="app-container">
    <div class="toggle">
      <button :class="{ active: mode === 'login' }" @click="switchMode('login')">Вход</button>
      <button :class="{ active: mode === 'register' }" @click="switchMode('register')">Регистрация</button>
    </div>

    <!-- форма логина -->
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
        {{ loading ? 'Загрузка...' : 'Войти' }}
      </button>
    </form>

    <!-- форма регистрации -->
    <form v-else @submit.prevent="codeSent ? verifyCode() : register()" class="form">
      <div v-if="!codeSent">
        <div class="form-group">
          <label>Имя</label>
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

        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
        </button>
      </div>

      <!-- поле ввода кода подтверждения -->
      <div v-else>
        <div class="form-group">
          <label>Введите код из письма</label>
          <input type="text" v-model="verificationCode" placeholder="Код из письма" required />
        </div>
        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? 'Проверка...' : 'Подтвердить код' }}
        </button>
        <button type="button" @click="codeSent = false" class="back-btn">
          Назад к регистрации
        </button>
      </div>
    </form>

    <p v-if="message" :class="['message', messageType]">{{ message }}</p>
  </div>
</template>

<script>
import axios from 'axios'
import { ref, reactive, computed } from 'vue'

export default {
  setup() {
    const mode = ref('login')
    const codeSent = ref(false)
    const message = ref('')
    const verificationCode = ref('')
    const loading = ref(false)
    const API_BASE = 'http://localhost:8000/api/'

    const loginData = reactive({ email: '', password: '' })
    const registerData = reactive({ email: '', username: '', password: '' })

    // Определяем тип сообщения для стилей
    const messageType = computed(() => {
      return message.value.includes('Успеш') || message.value.includes('отправлен') 
        ? 'success' 
        : 'error'
    })

    const switchMode = (m) => {
      mode.value = m
      codeSent.value = false
      message.value = ''
      loading.value = false
    }

    const validatePassword = (password) => {
      if (password.length < 6) {
        return 'Пароль должен быть не менее 6 символов'
      }
      return null
    }

    const login = async () => {
      if (loading.value) return
      
      loading.value = true
      try {
        const response = await axios.post(`${API_BASE}/login`, loginData)
        message.value = 'Успешный вход!'
        // Здесь можно сохранить токен и перенаправить
        console.log('Токен:', response.data.access_token)
      } catch (e) {
        if (e.response?.status === 401) {
          message.value = 'Неверный email или пароль.'
        } else if (e.response?.status === 403) {
          message.value = 'Аккаунт не активирован. Проверьте email.'
        } else {
          message.value = 'Ошибка входа. Попробуйте позже.'
        }
      } finally {
        loading.value = false
      }
    }

    const register = async () => {
      if (loading.value) return
      
      const passwordError = validatePassword(registerData.password)
      if (passwordError) {
        message.value = passwordError
        return
      }
      
      loading.value = true
      try {
        await axios.post(`${API_BASE}/register`, registerData)
        codeSent.value = true
        message.value = 'Код подтверждения отправлен на почту.'
      } catch (e) {
        if (e.response?.status === 400) {
          message.value = 'Пользователь с таким email уже существует.'
        } else {
          message.value = `Ошибка регистрации (${e.response?.status || 'нет ответа'}). Попробуйте позже.`
        }
      } finally {
        loading.value = false
      }
    }

    const verifyCode = async () => {
      if (loading.value) return
      
      loading.value = true
      try {
        await axios.post(`${API_BASE}/verify`, {
          email: registerData.email,
          code: verificationCode.value,
        })
        message.value = 'Регистрация подтверждена! Теперь войдите.'
        codeSent.value = false
        mode.value = 'login'
        Object.assign(registerData, { email: '', username: '', password: '' })
        verificationCode.value = ''
      } catch (e) {
        message.value = 'Неверный код. Попробуйте снова.'
      } finally {
        loading.value = false
      }
    }

    return {
      mode,
      codeSent,
      message,
      messageType,
      verificationCode,
      loginData,
      registerData,
      loading,
      switchMode,
      login,
      register,
      verifyCode,
    }
  },
}
</script>

<style scoped>
.app-container {
  max-width: 400px;
  margin: 50px auto;
  font-family: Arial, sans-serif;
}

.toggle {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.toggle button {
  flex: 1;
  padding: 10px;
  cursor: pointer;
  border: none;
  background: none;
  font-size: 16px;
  font-weight: bold;
  text-decoration: underline;
  transition: all 0.2s;
}

.toggle button.active {
  color: white;
  background-color: #007bff;
  border-radius: 5px 5px 0 0;
  text-decoration: none;
}

.form {
  border: 1px solid #ccc;
  padding: 20px;
  border-radius: 0 5px 5px 5px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  font-weight: bold;
  margin-bottom: 5px;
}

.form-group input {
  width: 100%;
  padding: 8px;
  box-sizing: border-box;
}

.submit-btn {
  width: 100%;
  padding: 10px;
  background-color: #007bff;
  border: none;
  color: white;
  font-weight: bold;
  cursor: pointer;
  border-radius: 5px;
  margin-bottom: 10px;
}

.submit-btn:hover:not(:disabled) {
  background-color: #0056b3;
}

.submit-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.back-btn {
  width: 100%;
  padding: 10px;
  background-color: #6c757d;
  border: none;
  color: white;
  font-weight: bold;
  cursor: pointer;
  border-radius: 5px;
}

.back-btn:hover {
  background-color: #545b62;
}

.message {
  margin-top: 15px;
  text-align: center;
  font-weight: bold;
  padding: 10px;
  border-radius: 5px;
}

.message.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.message.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}
</style>