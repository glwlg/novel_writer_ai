<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="rules"
    label-position="top"
    @submit.prevent="submitForm"
  >
    <el-form-item label="姓名" prop="name">
      <el-input v-model="formData.name" placeholder="角色全名" />
    </el-form-item>

    <el-form-item label="描述" prop="description">
      <el-input
        v-model="formData.description"
        type="textarea"
        :rows="3"
        placeholder="简短描述、外貌、关键特征"
      />
    </el-form-item>

    <el-form-item label="背景故事" prop="backstory">
      <el-input
        v-model="formData.backstory"
        type="textarea"
        :rows="5"
        placeholder="相关历史、起源、关键事件"
      />
    </el-form-item>

    <el-form-item label="目标" prop="goals">
      <el-input
        v-model="formData.goals"
        type="textarea"
        :rows="3"
        placeholder="角色想要达成什么？"
      />
    </el-form-item>

    <el-form-item label="角色弧光概要" prop="arc_summary">
       <el-input
        v-model="formData.arc_summary"
        type="textarea"
        :rows="3"
        placeholder="角色在故事中预计会如何变化？"
      />
    </el-form-item>

     <el-form-item label="当前状态" prop="current_status">
      <el-input
        v-model="formData.current_status"
        placeholder="例如：位置、状况、关系状态"
      />
    </el-form-item>

    <el-form-item class="form-actions">
      <el-button @click="cancelForm">取消</el-button>
      <el-button type="primary" native-type="submit" :loading="isSubmitting">
        {{ isEditing ? '保存更改' : '创建角色' }}
      </el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive, watch, computed, nextTick } from 'vue';
import { defineProps, defineEmits } from 'vue';
import { ElForm, ElFormItem, ElInput, ElButton } from 'element-plus';

const props = defineProps({
  initialData: {
    type: Object,
    default: null, // 使用 null 表示创建模式
  },
});

const emit = defineEmits(['submit', 'cancel']);

const formRef = ref(null);
const isSubmitting = ref(false); // 可选：提交按钮的加载状态

// 根据 CharacterBase/CharacterUpdate schemas 定义结构
const getDefaultFormData = () => ({
  name: '',
  description: '',
  backstory: '',
  goals: '',
  arc_summary: '',
  current_status: '',
  // project_id 不在这里包含，由父组件/store 处理
});

const formData = reactive(getDefaultFormData());

const isEditing = computed(() => !!props.initialData?.id); // 检查是否有 ID 来判断是否编辑模式

// 验证规则
const rules = reactive({
  name: [
    { required: true, message: '角色名称是必填项', trigger: 'blur' },
    { min: 1, max: 100, message: '长度应为 1 到 100', trigger: 'blur' },
  ],
  // 如果需要，为其他字段添加更多规则（例如最大长度）
  description: [{ max: 1000, message: '最大长度 1000 字符', trigger: 'blur' }],
  backstory: [{ max: 5000, message: '最大长度 5000 字符', trigger: 'blur' }],
  goals: [{ max: 1000, message: '最大长度 1000 字符', trigger: 'blur' }],
  arc_summary: [{ max: 2000, message: '最大长度 2000 字符', trigger: 'blur' }],
  current_status: [{ max: 255, message: '最大长度 255 字符', trigger: 'blur' }],
});

// --- 方法 ---
const initializeForm = (data) => {
    Object.assign(formData, getDefaultFormData()); // 先重置为默认值
    if (data) {
        // 只将 initialData 中可编辑的字段映射到 formData
        Object.keys(formData).forEach(key => {
            if (data[key] !== undefined && data[key] !== null) {
                formData[key] = data[key];
            }
        });
    }
    // 更新数据后重置验证状态
    nextTick(() => {
        formRef.value?.clearValidate();
    });
};

const submitForm = async () => {
  if (!formRef.value) return;
  isSubmitting.value = true;
  try {
    await formRef.value.validate();
    // 表单有效，发送数据
    // 创建一个干净的副本以发送，确保没有多余的属性
    const dataToEmit = { ...formData };
    // 关键：这里不包含 project_id 或 id。
    // 父组件/store action 会处理这些。
    emit('submit', dataToEmit);
  } catch (validationError) {
    console.log('表单验证失败:', validationError);
    // 不需要发送错误，ElForm 会处理显示错误信息
  } finally {
     isSubmitting.value = false;
  }
};

const cancelForm = () => {
  emit('cancel');
};

// 公开方法，供父组件在需要时重置验证（但 destroy-on-close 通常更好用）
// const resetFormValidation = () => {
//     formRef.value?.clearValidate();
// }
// defineExpose({ resetFormValidation });

// --- 监听器 ---
// 监听 initialData prop 以便在它变化时重新初始化表单
// 这对于对话框重用于创建/编辑至关重要
watch(
  () => props.initialData,
  (newData) => {
    initializeForm(newData);
  },
  { immediate: true, deep: true } // immediate 确保在挂载时运行
);

</script>

<style scoped>
.form-actions {
  margin-top: 20px;
  text-align: right;
}
/* 如果需要，添加更具体的样式 */
</style>