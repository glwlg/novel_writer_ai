<template>
  <el-form
    ref="chapterFormRef"
    :model="formData"
    :rules="rules"
    label-position="top"
    @submit.prevent="handleSubmit"
  >
    <el-form-item label="章节标题" prop="title">
      <el-input v-model="formData.title" placeholder="请输入章节标题" />
    </el-form-item>

    <el-form-item label="章节概要" prop="summary">
      <el-input
        v-model="formData.summary"
        type="textarea"
        :rows="4"
        placeholder="请输入章节概要（可选）"
      />
    </el-form-item>

    <!-- 编辑模式下可能显示章节 ID (只读) -->
    <!-- <el-form-item v-if="isEditing" label="章节 ID">
      <el-input :value="initialData.id" disabled />
    </el-form-item> -->

     <!-- 隐藏 project_id，创建时自动添加 -->

    <el-form-item>
      <el-button type="primary" native-type="submit" :loading="isLoading">
        {{ isEditing ? '更新' : '创建' }}
      </el-button>
      <el-button @click="handleCancel">取消</el-button>
    </el-form-item>

     <!-- 显示 API 错误 -->
     <el-alert v-if="apiError" :title="apiError" type="error" show-icon :closable="false"/>

  </el-form>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue';
import {
  ElForm,
  ElFormItem,
  ElInput,
  ElButton,
  ElAlert
} from 'element-plus';

// --- Props ---
const props = defineProps({
  initialData: { // 用于编辑模式，包含 id, title, summary, project_id, order 等
    type: Object,
    default: null
  },
  projectId: { // 创建模式下必须提供
    type: Number,
    required: true // 使其在创建时必须传入
  },
  isLoading: { // 由父组件控制的加载状态
    type: Boolean,
    default: false
  },
  apiError: { // 由父组件传入的 API 错误信息
      type: String,
      default: ''
  }
});

// --- Emits ---
const emit = defineEmits(['save', 'cancel']);

// --- Refs ---
const chapterFormRef = ref(null); // Ref for the form instance

// --- State ---
// 使用 reactive 确保深度监听，但要小心直接赋值覆盖响应性
// 更好的方式是使用 ref 包裹一个对象
const formData = ref({
  title: '',
  summary: ''
  // 不在这里包含 project_id 或 id，它们由 props 或逻辑决定
});

// --- Computed ---
const isEditing = computed(() => !!props.initialData?.id);

// --- Rules ---
const rules = reactive({
  title: [
    { required: true, message: '章节标题不能为空', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  summary: [
     // 概要是可选的
    { max: 5000, message: '概要不能超过 5000 个字符', trigger: 'blur' }
  ]
});

// --- Watcher ---
// 当 initialData 变化时（从 null 变为对象，或对象内容变化），更新表单
watch(() => props.initialData, (newData) => {
  if (newData && newData.id) {
    // 编辑模式：填充表单
    formData.value.title = newData.title || '';
    formData.value.summary = newData.summary || '';
  } else {
    // 创建模式：重置表单
    formData.value.title = '';
    formData.value.summary = '';
    // 如果表单实例存在，清除校验状态
    chapterFormRef.value?.resetFields();
  }
}, { immediate: true, deep: true }); // immediate: 首次加载时执行, deep: 深度监听 initialData

// --- Methods ---
const handleSubmit = async () => {
  if (!chapterFormRef.value) return;

  try {
    // 触发表单验证
    await chapterFormRef.value.validate();

    // 验证通过，准备数据并发送事件
    let payload;
    if (isEditing.value) {
      // 编辑模式: 发送 ChapterUpdate schema 需要的数据
      payload = {
        title: formData.value.title,
        summary: formData.value.summary
        // 注意：根据后端 API，可能还需要包含 order 等字段
        // order: props.initialData.order // 如果需要传递 order
      };
       emit('save', { id: props.initialData.id, data: payload });
    } else {
      // 创建模式: 发送 ChapterCreate schema 需要的数据
      payload = {
        project_id: props.projectId, // **重要：创建时需要 project_id**
        title: formData.value.title,
        summary: formData.value.summary
        // 注意：后端的 order 可能由服务层自动处理，或需要前端指定一个初始值（如 0 或列表长度）
      };
       emit('save', { data: payload }); // 不传 ID 表示创建
    }

  } catch (validationError) {
    console.log('表单验证失败:', validationError);
    // Element Plus 会自动显示错误信息，无需额外处理
  }
};

const handleCancel = () => {
  // 重置表单可能需要，取决于父组件如何处理取消
  // chapterFormRef.value?.resetFields();
  emit('cancel');
};

// 暴露 resetFields 方法给父组件（如果需要在外部重置）
// defineExpose({
//   resetFields: () => chapterFormRef.value?.resetFields()
// });

</script>

<style scoped>
/* 如果需要，可以添加一些自定义样式 */
.el-form-item {
  margin-bottom: 20px;
}
.el-alert {
    margin-top: 15px;
}
</style>