<template>
  <transition name="el-fade-in">
    <div v-if="visible && message" class="error-message-container">
       <el-alert
         :title="title"
         :type="type"
         :description="message"
         :closable="closable"
         show-icon
         @close="handleClose"
       >
       </el-alert>
     </div>
  </transition>
</template>

<script setup>
import { ref, watch, defineProps, defineEmits } from 'vue';
import { ElAlert } from 'element-plus';

// Props definition
const props = defineProps({
  message: {
    type: String,
    default: '',
  },
  title: {
    type: String,
    default: '错误', // Default title
  },
  type: {
    type: String,
    default: 'error', // 'success', 'warning', 'info', 'error'
    validator: (value) => ['success', 'warning', 'info', 'error'].includes(value),
  },
  closable: {
    type: Boolean,
    default: true, // Allow user to close the message
  },
  duration: { // Auto-close duration (ms). 0 or null means manual close.
      type: Number,
      default: 0
  }
});

// Emits definition
const emit = defineEmits(['close']);

// --- Refs ---
const visible = ref(false);
let timer = null;

// --- Methods ---
const handleClose = () => {
  visible.value = false;
  clearTimeout(timer);
  emit('close'); // Notify parent it was closed
};

const show = () => {
    visible.value = true;
    if (props.duration > 0) {
        clearTimeout(timer); // Clear previous timer if any
        timer = setTimeout(() => {
            handleClose();
        }, props.duration);
    }
}

// --- Watchers ---
watch(() => props.message, (newMessage) => {
    if (newMessage) {
       show();
    } else {
        // If message is cleared externally, hide the alert
        visible.value = false;
        clearTimeout(timer);
    }
});

// --- Lifecycle ---
// Optional: Show on mount if message is initially present
import { onMounted } from 'vue';
onMounted(() => {
    if (props.message) {
        show();
    }
});

// Cleanup timer on unmount
import { onBeforeUnmount } from 'vue';
onBeforeUnmount(() => {
    clearTimeout(timer);
});


</script>

<style scoped>
.error-message-container {
  /* Add margin or positioning if needed */
  margin-bottom: 15px;
}
/* ElAlert styling is generally handled by Element Plus themes */
</style>