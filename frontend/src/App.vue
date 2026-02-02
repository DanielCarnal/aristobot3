<template>
  <div id="app" class="app">
    <!-- Layout complet pour les pages authentifiées -->
    <template v-if="showLayout">
      <Sidebar />
      <div class="main-content">
        <StatusBar />
        <div class="content">
          <router-view />
        </div>
      </div>
    </template>
    
    <!-- Vue simple pour la page de login -->
    <template v-else>
      <router-view />
    </template>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import StatusBar from './components/StatusBar.vue'
import { useAuthStore } from './stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isLoginPage = computed(() => route.path === '/login')
const showLayout = computed(() => authStore.isAuthenticated && !isLoginPage.value)

onMounted(async () => {
  try {
    // D'abord vérifier le mode debug
    await authStore.checkDebugConfig()
    
    // Si mode debug actif, login automatique avec 'dev'
    if (authStore.debugEnabled && authStore.debugActive) {
      const debugLoginSuccess = await authStore.debugLogin()
      
      if (debugLoginSuccess) {
        // Rediriger vers l'app si on était sur login
        if (route.path === '/login') {
          router.push('/')
        }
        return
      }
    }
    
    // Sinon, vérification auth normale
    const isAuth = await authStore.checkAuth()
    
    // Si pas authentifié et pas sur la page login, rediriger
    if (!isAuth && route.path !== '/login') {
      router.push('/login')
    }
    // Si authentifié et sur la page login, rediriger vers l'app
    else if (isAuth && route.path === '/login') {
      router.push('/')
    }
  } catch (error) {
    console.error('App.vue - Erreur auth check:', error)
    if (route.path !== '/login') {
      router.push('/login')
    }
  }
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: var(--color-background);
  color: var(--color-text);
}

.app {
  display: flex;
  height: 100vh;
  background-color: var(--color-background);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

:root {
  --color-primary: #00D4FF;
  --color-success: #00FF88;
  --color-danger: #FF0055;
  --color-warning: #FFB800;
  --color-background: #0A0A0A;
  --color-surface: #1A1A1A;
  --color-text: #FFFFFF;
  --color-text-secondary: #CCCCCC;
  --color-border: #333333;
}
</style>