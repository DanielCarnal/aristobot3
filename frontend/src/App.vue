<template>
  <div id="app" class="app">
    <Sidebar />
    <div class="main-content">
      <StatusBar />
      <div class="content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import Sidebar from './components/Sidebar.vue'
import StatusBar from './components/StatusBar.vue'
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
  --color-background: #0A0A0A;
  --color-surface: #1A1A1A;
  --color-text: #FFFFFF;
  --color-text-secondary: #CCCCCC;
  --color-border: #333333;
}
</style>