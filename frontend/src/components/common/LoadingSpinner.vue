<template>
  <div v-if="loading" class="loading-overlay" :class="{ fullscreen: fullscreen }">
    <div class="spinner-container">
      <el-icon class="is-loading spinner-icon" :size="size">
        <Loading />
      </el-icon>
      <p v-if="text" class="loading-text">{{ text }}</p>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue';
import { ElIcon } from 'element-plus';
import { Loading } from '@element-plus/icons-vue';

// Props definition
const props = defineProps({
  loading: {
    type: Boolean,
    default: true, // Often controlled by parent, but can show by default
  },
  text: {
    type: String,
    default: '', // Optional text like 'Loading...'
  },
  size: {
    type: [String, Number],
    default: 30, // Size of the icon
  },
  fullscreen: { // Whether the spinner covers the whole screen or just its container
      type: Boolean,
      default: false,
  }
});
</script>

<style scoped>
.loading-overlay {
  position: absolute; /* Relative to parent container */
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.7); /* Semi-transparent background */
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000; /* Ensure it's above other content */
  border-radius: 4px; /* Match container radius if needed */
}

.loading-overlay.fullscreen {
  position: fixed; /* Covers the entire viewport */
   border-radius: 0;
}

.spinner-container {
  text-align: center;
}

.spinner-icon {
  color: var(--el-color-primary); /* Use theme color */
}

.loading-text {
  margin-top: 10px;
  color: var(--el-text-color-regular);
  font-size: 0.9rem;
}
</style>