<template>
  <!-- 卷信息编辑表单 -->
  <el-form ref="volumeFormRef" :model="formData" :rules="volumeFormRules" label-position="top">
    <!-- 卷名输入框 -->
    <el-form-item label="卷名" prop="title">
      <el-input v-model="formData.title" placeholder="请输入卷名"/>
    </el-form-item>
    <!-- 卷概要输入框 -->
    <el-form-item label="卷概要" prop="summary">
      <el-input v-model="formData.summary" type="textarea" :rows="3" placeholder="（可选）输入卷的概要"/>
    </el-form-item>
    <!-- 排序权重输入框 -->
    <el-form-item label="排序权重" prop="order">
      <el-input-number v-model="formData.order" :min="0" controls-position="right"/>
      <el-text size="small" type="info" style="margin-left: 10px;">数字越小越靠前</el-text>
    </el-form-item>
  </el-form>
  <!-- 对话框底部操作按钮 -->
  <div class="dialog-footer">
    <el-button @click="handleCancel">取消</el-button>
    <el-button type="primary" @click="handleSubmit" :loading="isLoading">
      {{ isEditing ? '保存修改' : '创建卷' }}
    </el-button>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';
import { ElForm, ElFormItem, ElInput, ElInputNumber, ElButton, ElText } from 'element-plus';

// --- 组件属性定义 ---
const props = defineProps({
  // 表单初始数据
  initialData: {
    type: Object,
    default: () => ({ id: null, title: '', summary: '', order: 0 })
  },
  // 是否处于编辑模式
  isEditing: {
    type: Boolean,
    default: false
  },
  // 是否正在加载（用于保存按钮）
  isLoading: {
    type: Boolean,
    default: false
  }
});

// --- 组件事件定义 ---
const emit = defineEmits(['save', 'cancel']);

// --- 内部状态 ---
// 表单数据模型
const formData = ref({ ...props.initialData });
// 表单DOM引用
const volumeFormRef = ref(null);

// --- 表单验证规则 ---
const volumeFormRules = ref({
  title: [{ required: true, message: '卷名不能为空', trigger: 'blur' }],
  // summary 和 order 不是必填项
});

// --- 监听器 ---
// 监听 initialData 变化，同步更新表单数据
watch(() => props.initialData, (newData) => {
  formData.value = { ...newData };
  // 数据变化后，清除可能的旧校验信息
  nextTick(() => {
    volumeFormRef.value?.clearValidate();
  });
}, { deep: true, immediate: true }); // 立即执行并在深层级上监听

// --- 方法 ---
// 处理取消事件
const handleCancel = () => {
  emit('cancel');
};

// 处理提交事件
const handleSubmit = async () => {
  if (!volumeFormRef.value) return;
  try {
    // 触发表单验证
    const valid = await volumeFormRef.value.validate();
    if (valid) {
      // 验证通过，触发 save 事件并传递当前表单数据
      emit('save', { ...formData.value });
    }
  } catch (error) {
    // 验证失败，Element Plus 的 validate 会 reject promise
    console.log('表单验证失败:', error);
  }
};

// --- 暴露的方法 (可选) ---
// 提供给父组件调用的重置表单方法
const resetForm = () => {
  if (volumeFormRef.value) {
    volumeFormRef.value.resetFields(); // 重置表单字段值和校验状态
  }
  // 也可以手动重置为初始值
  // formData.value = { ...props.initialData };
};

// 暴露 resetForm 方法给父组件
defineExpose({
  resetForm
});

</script>

<style scoped>
/* 对话框底部样式 */
.dialog-footer {
  text-align: right;
  margin-top: 20px; /* 与表单内容保持间距 */
}
</style>