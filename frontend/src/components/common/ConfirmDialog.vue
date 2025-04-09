<template>
  <el-dialog
    v-model="dialogVisible"
    :title="title"
    :width="width"
    :before-close="handleCancel"
    custom-class="confirm-dialog"
    :close-on-click-modal="false"
    :append-to-body="appendToBody"
    draggable
  >
    <div class="dialog-content">
      <el-icon v-if="showIcon" :size="22" class="warning-icon"><WarningFilled /></el-icon>
      <span>{{ message }}</span>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleCancel" :disabled="loading">{{ cancelButtonText }}</el-button>
        <el-button
          type="primary"
          @click="handleConfirm"
          :loading="loading"
          :disabled="loading"
        >
          {{ confirmButtonText }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, defineProps, defineEmits } from 'vue';
import { ElDialog, ElButton, ElIcon } from 'element-plus';
import { WarningFilled } from '@element-plus/icons-vue'; // Example icon

// Props definition
const props = defineProps({
  modelValue: { // Use v-model:modelValue for visibility
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '确认操作',
  },
  message: {
    type: String,
    required: true,
  },
  confirmButtonText: {
    type: String,
    default: '确认',
  },
  cancelButtonText: {
    type: String,
    default: '取消',
  },
  width: {
    type: String,
    default: '30%', // Adjust as needed
  },
  showIcon: {
      type: Boolean,
      default: true,
  },
  appendToBody: { // Useful if the dialog is inside complex layouts
      type: Boolean,
      default: true,
  }
});

// Emits definition
const emit = defineEmits(['update:modelValue', 'confirm', 'cancel']);

// --- Refs ---
const dialogVisible = ref(props.modelValue);
const loading = ref(false); // Internal loading state for confirm action

// --- Watchers ---
// Sync internal visibility with v-model prop
watch(() => props.modelValue, (newVal) => {
  dialogVisible.value = newVal;
  if (!newVal) {
    loading.value = false; // Reset loading state when dialog is hidden externally
  }
});

// --- Methods ---
const handleConfirm = async () => {
  loading.value = true;
  try {
    // Emit confirm event and let the parent handle the async logic
    // The parent should set loading=false by closing the dialog (setting modelValue=false)
    // or by directly controlling a loading prop if needed.
    emit('confirm');
    // Optional: await parent logic if passed as a function prop? More complex.
    // For simplicity, parent hides dialog on success/failure.
  } catch (error) {
      console.error("Confirmation action failed:", error);
      loading.value = false; // Ensure loading stops on error within dialog if needed
      // Optionally emit an error event
  }
  // We typically expect the parent to close the dialog by setting modelValue to false
  // upon successful confirmation. Setting loading back to false might happen too early here.
};

const handleCancel = () => {
  if (loading.value) return; // Don't cancel while confirming
  dialogVisible.value = false;
  emit('update:modelValue', false); // Update v-model
  emit('cancel');
};

</script>

<style scoped>
.dialog-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.warning-icon {
  color: var(--el-color-warning);
  flex-shrink: 0; /* Prevent icon from shrinking */
}

/* Optional: Customize dialog appearance */
:deep(.el-dialog__body) {
    padding-bottom: 10px; /* Adjust spacing */
}
:deep(.el-dialog__footer) {
    padding-top: 10px;
}
</style>