<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="rules"
    label-position="top"
    :disabled="loading || isSaving"
    v-loading="loading"
    element-loading-text="加载中..."
  >
    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="场景标题" prop="title">
          <el-input v-model="formData.title" placeholder="给场景起个名字（可选）" />
        </el-form-item>
      </el-col>
      <el-col :span="12">
         <el-form-item label="所属章节" prop="chapter_id">
          <el-select
            v-model="formData.chapter_id"
            placeholder="选择章节或留空（未分配）"
            clearable
            filterable
            style="width: 100%;"
          >
            <el-option
              v-for="chapter in availableChapters"
              :key="chapter.id"
              :label="chapter.title"
              :value="chapter.id"
            />
          </el-select>
        </el-form-item>
      </el-col>
    </el-row>

    <el-form-item label="场景目标/核心内容" prop="goal">
      <el-input
        v-model="formData.goal"
        type="textarea"
        :rows="3"
        placeholder="简要描述这个场景需要达成的目标或核心情节"
        required
      />
    </el-form-item>

    <el-form-item label="场景概要/备注" prop="summary">
      <el-input
        v-model="formData.summary"
        type="textarea"
        :rows="2"
        placeholder="场景的简短总结或备注（可选）"
      />
    </el-form-item>

    <el-row :gutter="20">
       <el-col :span="12">
          <el-form-item label="状态" prop="status">
            <el-select v-model="formData.status" placeholder="选择场景状态" style="width: 100%;">
              <el-option label="计划中" value="PLANNED" />
              <el-option label="草稿" value="DRAFTED" />
              <el-option label="修订中" value="REVISING" />
              <el-option label="已完成" value="COMPLETED" />
               <!-- 考虑是否允许手动设置生成中/失败状态 -->
               <!-- <el-option label="生成中" value="GENERATING" disabled /> -->
               <!-- <el-option label="生成失败" value="GENERATION_FAILED" disabled /> -->
            </el-select>
          </el-form-item>
       </el-col>
        <el-col :span="12">
           <!-- 章节内排序，如果需要在此编辑的话 -->
           <el-form-item label="章节内排序" prop="order_in_chapter">
             <el-input-number v-model="formData.order_in_chapter" :min="0" controls-position="right" style="width: 100%;" />
           </el-form-item>
        </el-col>
    </el-row>

    <el-form-item>
      <el-button type="primary" @click="submitForm" :loading="isSaving">保存元数据</el-button>
      <el-button @click="resetForm" :disabled="isSaving">重置表单</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { useSceneStore } from '@/store/scene'; // 导入 Scene Store
import { useChapterStore } from '@/store/chapter'; // 导入 Chapter Store 获取章节列表
import { ElMessage } from 'element-plus';

// --- Props ---
const props = defineProps({
  scene: { // 接收来自父组件的当前场景对象 (SceneRead)
    type: Object,
    default: () => null,
  },
  loading: { // 父组件传递的加载状态
    type: Boolean,
    default: false,
  },
  projectId: { // 需要项目ID来获取章节列表
      type: [String, Number],
      required: true,
  }
});

// --- Emits ---
const emit = defineEmits(['updated']); // 通知父组件已更新

// --- Stores ---
const sceneStore = useSceneStore();
const chapterStore = useChapterStore();

// --- Refs ---
const formRef = ref(null);
const isSaving = ref(false); // 本地保存状态

// --- Form Data ---
// 使用 ref 来创建响应式对象，以便 watch 可以检测到 props.scene 的变化
const formData = ref({
  title: '',
  goal: '',
  summary: '',
  status: 'PLANNED',
  chapter_id: null,
  order_in_chapter: 0,
});

// --- Validation Rules ---
const rules = ref({
  goal: [{ required: true, message: '场景目标不能为空', trigger: 'blur' }],
  // 可以根据需要添加其他规则
});

// --- Computed ---
// 从 Chapter Store 获取当前项目可用的章节列表
const availableChapters = computed(() => chapterStore.chapters);

// --- Watcher ---
// 当父组件传入的 scene 对象变化时，更新表单数据
watch(() => props.scene, (newScene) => {
  if (newScene) {
    formData.value = {
      title: newScene.title || '',
      goal: newScene.goal || '',
      summary: newScene.summary || '',
      status: newScene.status || 'PLANNED',
      chapter_id: newScene.chapter_id || null, // 后端可能返回 null
      order_in_chapter: newScene.order_in_chapter ?? 0, // 使用 nullish coalescing
    };
  } else {
    // 如果 scene 变为 null (例如，场景被删除或导航离开)
    resetForm(); // 重置表单
  }
}, { immediate: true, deep: true }); // immediate: 初始加载时执行一次; deep: 深度监听对象内部变化

// --- Methods ---
const submitForm = async () => {
  if (!formRef.value) return;
  try {
    await formRef.value.validate(); // 触发表单验证
    isSaving.value = true;

    // 准备需要发送的更新数据 (只发送有变化的字段，或者根据后端 API 定义发送)
    // 确保类型正确，例如 chapter_id 为 null 或 number
    const updateData = {
       title: formData.value.title,
       goal: formData.value.goal,
       summary: formData.value.summary,
       status: formData.value.status,
       chapter_id: formData.value.chapter_id === '' ? null : formData.value.chapter_id, // 处理空字符串情况
       order_in_chapter: formData.value.order_in_chapter,
    };

    // 调用 store action 更新场景
    await sceneStore.updateScene(props.scene.id, updateData);

    ElMessage.success('场景元数据已保存');
    emit('updated'); // 通知父组件更新完成

  } catch (validationError) {
      if (validationError === false) { // Element Plus validate promise rejects with false if validation fails
        console.log('表单验证失败');
        ElMessage.warning('请检查表单输入');
      } else {
        console.error('保存场景失败:', validationError);
        // 错误信息已在 store 中处理，这里可以不显示，或者显示通用错误
        // ElMessage.error(`保存失败: ${sceneStore.error || '未知错误'}`);
      }
  } finally {
    isSaving.value = false;
  }
};

const resetForm = () => {
  if (props.scene) {
     // 重置为 props 传入的原始数据
     formData.value = {
       title: props.scene.title || '',
       goal: props.scene.goal || '',
       summary: props.scene.summary || '',
       status: props.scene.status || 'PLANNED',
       chapter_id: props.scene.chapter_id || null,
       order_in_chapter: props.scene.order_in_chapter ?? 0,
     };
  } else {
    // 如果没有原始 scene 数据，则清空
    formData.value = {
      title: '', goal: '', summary: '', status: 'PLANNED', chapter_id: null, order_in_chapter: 0,
    };
  }
  // 清除表单验证状态
  formRef.value?.clearValidate();
};

</script>

<style scoped>
/* 可以添加一些样式 */
.el-form-item {
    margin-bottom: 18px;
}
</style>