<template>
  <el-form
    ref="settingFormRef"
    :model="formData"
    :rules="rules"
    label-width="100px"
    label-position="top"
    @submit.prevent="handleSubmit"
  >
    <el-form-item label="设定名称" prop="name">
      <el-input v-model="formData.name" placeholder="请输入设定名称" clearable />
    </el-form-item>

    <el-form-item label="设定类型" prop="element_type">
      <el-select v-model="formData.element_type" placeholder="请选择设定类型" style="width: 100%">
        <el-option
          v-for="item in settingTypes"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
    </el-form-item>

    <el-form-item label="描述" prop="description">
      <el-input
        v-model="formData.description"
        type="textarea"
        :rows="4"
        placeholder="请输入详细描述"
        show-word-limit
        maxlength="1000"
      />
    </el-form-item>

    <el-form-item>
      <el-button type="primary" native-type="submit">
        {{ isEditMode ? '更新设定' : '创建设定' }}
      </el-button>
      <el-button @click="handleCancel">取消</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue';
import { ElMessage, ElForm } from 'element-plus';

// --- Props ---
const props = defineProps({
  // 初始数据，用于编辑模式
  initialData: {
    type: Object,
    default: null,
  },
  // 是否为编辑模式
  isEditMode: {
    type: Boolean,
    default: false,
  },
});

// --- Emits ---
const emit = defineEmits(['submit', 'cancel']);

// --- Refs ---
const settingFormRef = ref(null); // 表单引用

// --- Reactive State ---
// 定义表单数据结构，匹配 SettingElementCreate / SettingElementUpdate
const formData = reactive({
  name: '',
  element_type: '',
  description: '',
});

// 设定类型选项 (与后端 schema 对应, label 为中文)
const settingTypes = ref([
  { value: 'Location', label: '地点' },
  { value: 'Item', label: '物品' },
  { value: 'Concept', label: '概念' },
  { value: 'Faction', label: '阵营/组织' },
  { value: 'Character Trait', label: '角色特质' },
  { value: 'World Rule', label: '世界规则' },
  { value: 'Lore', label: '背景传说' },
  { value: 'Technology', label: '技术设定' },
  { value: 'Magic System', label: '魔法体系' },
  { value: 'Other', label: '其他' },
]);

// --- Computed Properties ---
// 简单的中文转换函数或对象可以在这里定义，或者全局 utils
const getSettingTypeLabel = (value) => {
  const type = settingTypes.value.find(t => t.value === value);
  return type ? type.label : value; // 如果找不到，返回原始值
};

// --- Validation Rules ---
const rules = reactive({
  name: [
    { required: true, message: '请输入设定名称', trigger: 'blur' },
    { min: 1, max: 100, message: '名称长度应在 1 到 100 个字符之间', trigger: 'blur' },
  ],
  element_type: [
    { required: true, message: '请选择设定类型', trigger: 'change' },
  ],
  description: [
    // description 是可选的，但可以加长度限制
     { max: 1000, message: '描述不能超过 1000 个字符', trigger: 'blur' },
  ],
});

// --- Watchers ---
// 监听 initialData 的变化，用于填充表单（编辑模式）
watch(
  () => props.initialData,
  (newData) => {
    if (newData && props.isEditMode) {
      formData.name = newData.name || '';
      formData.element_type = newData.element_type || '';
      formData.description = newData.description || '';
    } else {
      // 如果不是编辑模式或 initialData 为空，重置表单
      formData.name = '';
      formData.element_type = '';
      formData.description = '';
      // 清除可能的校验状态
      settingFormRef.value?.resetFields();
    }
  },
  { immediate: true, deep: true } // 立即执行一次，深度监听
);

// --- Methods ---
// 处理表单提交
const handleSubmit = async () => {
  if (!settingFormRef.value) return;
  try {
    await settingFormRef.value.validate();
    // 校验通过，触发 submit 事件，传递表单数据
    // 注意：这里传递的是响应式对象的普通拷贝，防止父组件意外修改
    emit('submit', { ...formData });
  } catch (error) {
    // 校验失败
    console.error('表单校验失败:', error);
    ElMessage.error('请检查表单输入项');
  }
};

// 处理取消操作
const handleCancel = () => {
  // 触发 cancel 事件
  emit('cancel');
};

// --- Lifecycle Hooks ---
// (可选)
</script>

<style scoped>
/* 可以添加一些局部样式 */
.el-form-item {
  margin-bottom: 20px; /* 增加表单项间距 */
}
</style>