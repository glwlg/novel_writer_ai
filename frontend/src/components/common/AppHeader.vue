<template>
  <el-header class="app-header" height="60px">
    <div class="header-content">
      <div class="logo-title">
        <!-- You can replace this with an actual logo image -->
        <img src="@/assets/logo.png" alt="Logo" class="logo" v-if="showLogo" />
        <span class="title">{{ appTitle }}</span>
      </div>
      <div class="spacer"></div>
      <div class="actions">
        <!-- Placeholder for user actions like settings, profile, logout -->
        <slot name="actions">
          <!-- Default content if no actions slot is provided -->
           <el-button type="primary" plain size="small" @click="handleSettings">设置</el-button>
           <el-button type="info" plain size="small" @click="handleLogout">登出</el-button>
        </slot>
      </div>
    </div>
  </el-header>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';
import { ElHeader, ElButton } from 'element-plus'; // Auto-import likely handles this, but good practice

// Props definition
const props = defineProps({
  appTitle: {
    type: String,
    default: 'AI 小说家助手',
  },
  showLogo: {
    type: Boolean,
    default: true,
  },
});

// Emits definition (for potential actions)
const emit = defineEmits(['settings-click', 'logout-click']);

// --- Methods ---
const handleSettings = () => {
  console.log('Settings clicked');
  emit('settings-click');
  // Add navigation or modal logic here
};

const handleLogout = () => {
  console.log('Logout clicked');
  emit('logout-click');
  // Add logout logic here
};
</script>

<style scoped>
.app-header {
  background-color: #ffffff;
  border-bottom: 1px solid var(--el-border-color-light);
  padding: 0 20px; /* Adjust padding as needed */
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}

.header-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.logo-title {
  display: flex;
  align-items: center;
}

.logo {
  height: 32px; /* Adjust logo size */
  margin-right: 10px;
  vertical-align: middle; /* Helps align image and text */
}

.title {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
  white-space: nowrap;
}

.spacer {
  flex-grow: 1; /* Pushes actions to the right */
}

.actions {
  display: flex;
  align-items: center;
  gap: 10px; /* Space between action buttons */
}

/* Ensure buttons have appropriate styling if needed */
/* .el-button { ... } */
</style>