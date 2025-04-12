<template>
  <el-form
    ref="projectFormRef"
    :model="formData"
    :rules="rules"
    label-position="top"
    @submit.prevent="handleSubmit"
  >
    <el-form-item label="项目标题" prop="title">
      <el-input v-model="formData.title" placeholder="例如：赛博朋克侦探故事" />
    </el-form-item>
    <el-form-item label="风格" prop="style">
      <el-input
        v-model="formData.style"
        :rows="2"
        placeholder="小说风格：玄幻、赛博朋克、科幻、未来主义等"
      />
    </el-form-item>
    <el-form-item label="一句话简介 (Logline)" prop="logline">
      <el-input
        v-model="formData.logline"
        type="textarea"
        :rows="5"
        placeholder="用一句话概括你的故事核心"
      />
    </el-form-item>
    <el-form-item label="全局概要 (Synopsis)" prop="global_synopsis">
      <el-input
        v-model="formData.global_synopsis"
        type="textarea"
        :rows="5"
        placeholder="（可选）故事的整体梗概或背景设定概要"
      />
      <!-- Consider using RichTextEditor component here if needed -->
      <!-- <RichTextEditor v-model="formData.global_synopsis" /> -->
    </el-form-item>

    <el-form-item>
       <div style="display: flex; justify-content: flex-end; width: 100%;">
           <el-button @click="handleCancel">取消</el-button>
           <el-button type="primary" native-type="submit" :loading="isSubmitting">
              {{ isEditMode ? '更新项目' : '创建项目' }}
           </el-button>
       </div>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive, watch, computed, defineProps, defineEmits } from 'vue';
import { ElForm, ElFormItem, ElInput, ElButton } from 'element-plus'; // Auto-imported likely

const props = defineProps({
  projectToEdit: { // Pass the project object if editing, null/undefined if creating
    type: Object,
    default: null,
  },
   isSubmitting: { // Pass loading state from parent
      type: Boolean,
      default: false
  }
});

const emit = defineEmits(['submit', 'cancel']);

const projectFormRef = ref(null); // Reference to the form instance

const isEditMode = computed(() => !!props.projectToEdit);

// Initialize form data
const initialFormData = () => ({
  title: '',
  style: '',
  logline: '',
  global_synopsis: '',
});

const formData = reactive(initialFormData());

// Validation rules
const rules = reactive({
  title: [
    { required: true, message: '项目标题不能为空', trigger: 'blur' },
    { min: 2, max: 100, message: '标题长度应在 2 到 100 个字符之间', trigger: 'blur' },
  ],
  style: [
    { required: true, message: '风格不能为空', trigger: 'blur' },
    { min: 2, max: 20, message: '风格长度应在 2 到 20 个字符之间', trigger: 'blur' },
  ],
  // Add more rules if needed for logline or synopsis
});

// Watch for changes in projectToEdit prop to populate the form for editing
watch(
  () => props.projectToEdit,
  (newVal) => {
    if (newVal) {
      // Edit mode: Populate form with existing data
      formData.title = newVal.title || '';
      formData.style = newVal.style || '';
      formData.logline = newVal.logline || '';
      formData.global_synopsis = newVal.global_synopsis || '';
      // Reset validation state if needed when switching projects
       projectFormRef.value?.clearValidate();
    } else {
      // Create mode: Reset form to initial state
      Object.assign(formData, initialFormData());
        projectFormRef.value?.resetFields(); // Use resetFields for better state clearing
    }
  },
  { immediate: true, deep: true } // immediate to run on mount, deep if projectToEdit could change internally
);

// Form submission handler
const handleSubmit = async () => {
  if (!projectFormRef.value) return;
  try {
    await projectFormRef.value.validate();
    // Validation passed, emit the form data
    emit('submit', { ...formData }); // Emit a copy
    // Reset form after successful submission
    projectFormRef.value.resetFields(); // Use resetFields for better state clearing
    Object.assign(formData, initialFormData()); // Reset reactive data
  } catch (error) {
    // Validation failed
    console.log('Form validation failed:', error);
  }
};

// Cancel handler
const handleCancel = () => {
  emit('cancel');
};

// Function to reset the form (can be called from parent if needed)
// defineExpose({
//   resetForm: () => {
//      if (projectFormRef.value) {
//           projectFormRef.value.resetFields();
//      }
//      Object.assign(formData, initialFormData());
//   }
// });
</script>

<style scoped>
/* Add any specific styling for the form if needed */
.el-form-item {
  margin-bottom: 22px; /* Element Plus default, adjust if needed */
}
</style>