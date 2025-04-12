<template>
  <div class="scene-content-display">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>场景内容</span>
           <el-button v-if="!readOnly" type="primary" size="small" @click="saveContent" :loading="isSavingContent">保存内容</el-button>
        </div>
      </template>

      <div v-if="loading" class="content-loading">
        <el-skeleton :rows="5" animated />
      </div>
<!--      <div v-else-if="!content && !readOnly" class="content-placeholder">-->
<!--          <el-empty description="还没有生成内容，可以点击上方按钮开始生成。"></el-empty>-->
<!--      </div>-->
       <div v-else-if="!content && readOnly" class="content-placeholder">
          <el-text type="info">无生成内容。</el-text>
      </div>
      <div v-else>
         <RichTextEditor
           v-if="!readOnly"
           v-model="editableContent"
           :editorProps="{
             attributes: {
               class: 'prose prose-sm sm:prose lg:prose-lg xl:prose-2xl m-5 focus:outline-none',
             },
           }"
         />
          <div v-else class="read-only-content prose" v-html="processedContent"></div>
      </div>

    </el-card>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import RichTextEditor from '@/components/common/RichTextEditor.vue';
import {ElMessage} from "element-plus";
import {MagicStick} from "@element-plus/icons-vue"; // 确保路径正确
// import DOMPurify from 'dompurify'; // 如果需要清理 v-html 的内容

// --- Props ---
const props = defineProps({
  content: { // 接收生成的原始内容 (可能是 HTML 或 Markdown)
    type: String,
    default: '',
  },
  loading: { // 是否正在加载内容 (例如，父组件正在获取场景详情)
    type: Boolean,
    default: false,
  },
  readOnly: { // 控制是否允许编辑
    type: Boolean,
    default: false, // 默认允许编辑，父组件可以控制
  },
});

// --- Emits ---
// 用于 v-model 绑定，如果 RichTextEditor 支持
const emit = defineEmits(['update:content']);

// --- Refs ---
const editableContent = ref('');
const isSavingContent = ref(false); // 如果在此组件处理保存

// --- Watcher ---
// 当外部 content 变化时，更新内部的 editableContent (用于编辑器)
watch(() => props.content, (newVal) => {
  editableContent.value = newVal || '';
}, { immediate: true });

// 监听内部 editableContent 的变化，并通过 v-model 更新父组件
// (如果 RichTextEditor 使用 v-model)
watch(editableContent, (newVal) => {
  if (newVal !== props.content) {
    emit('update:content', newVal);
  }
});

// --- Computed ---
// 处理只读内容，例如清理 HTML
const processedContent = computed(() => {
    if (props.readOnly && props.content) {
        // return DOMPurify.sanitize(props.content); // 使用 DOMPurify 清理
        return props.content; // 如果信任内容源，可以直接返回
    }
    return '';
});

// --- Methods ---
// 如果需要在此组件内保存内容
const saveContent = async () => {
  isSavingContent.value = true;
  try {
    // 调用 API 或 emit 事件给父组件处理保存
    emit('save-content', editableContent.value); // 示例：发出保存事件
    ElMessage.success('内容已保存');
  } catch (error) {
    console.error('保存内容失败:', error);
    ElMessage.error('保存内容失败');
  } finally {
    isSavingContent.value = false;
  }
};

</script>

<style scoped>
.scene-content-display {
  margin-top: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.content-loading, .content-placeholder {
  padding: 20px;
  text-align: center;
}
/* 确保编辑器/显示区域有最小高度 */
.read-only-content, ::v-deep(.prose) { /* 使用 ::v-deep 或 :deep() 穿透 scoped 样式 */
  min-height: 200px;
   border: 1px solid #dcdfe6; /* 可选：给只读内容添加边框 */
   padding: 10px;
   border-radius: 4px;
   background-color: #f9f9f9; /* 可选：背景色 */
}

/* Tiptap/ProseMirror 的基础样式可能需要全局引入或在此处覆盖 */
/* 例如：*/
::v-deep(.tiptap) {
    padding: 10px;
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    min-height: 200px;
}
::v-deep(.tiptap:focus-visible) {
    outline: none;
    border-color: var(--el-color-primary);
}

/* 添加 Prose 样式 (如果使用了 Tailwind Typography) */
/* 你可能需要在 tailwind.config.js 中配置 */
.prose {
    /* 默认样式，可能需要根据你的 UI 调整 */
    max-width: none; /* 取消最大宽度限制 */
}

/* 简单 <pre> 标签样式 */
.read-only-content-pre {
  white-space: pre-wrap; /* 保持换行 */
  word-wrap: break-word; /* 长单词换行 */
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  font-family: monospace;
  min-height: 200px;
  border: 1px solid #e4e7ed;
}

</style>