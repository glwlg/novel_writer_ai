<template>
  <div class="chapter-item">
    <div class="chapter-info">
      <span class="chapter-title">{{ chapter.title }}</span>
      <p v-if="truncatedSummary" class="chapter-summary">{{ truncatedSummary }}</p>
      <!-- 可选：显示章节顺序 -->
      <!-- <span class="chapter-order">Order: {{ chapter.order }}</span> -->
    </div>
    <div class="chapter-actions">
      <el-tooltip content="编辑章节" placement="top">
        <el-button icon="Edit" circle plain size="small" @click="handleEdit" />
      </el-tooltip>
      <el-tooltip content="删除章节" placement="top">
        <el-button type="danger" icon="Delete" circle plain size="small" @click="handleDelete" />
      </el-tooltip>
      <!-- 未来可添加拖拽句柄 -->
      <!-- <el-icon class="drag-handle"><Rank /></el-icon> -->
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { ElButton, ElTooltip, ElIcon } from 'element-plus';
// import { Rank, Edit, Delete } from '@element-plus/icons-vue'; // 如果需要拖拽或图标

// --- Props ---
// 假设 chapter prop 至少包含 id, title, summary, order
// 最好是使用从 schemas/chapter.py 导出的类型，例如 ChapterReadMinimal
const props = defineProps({
  chapter: {
    type: Object,
    required: true,
    default: () => ({ id: null, title: '', summary: '', order: 0 }) // Provide a default structure
  },
  summaryMaxLength: {
    type: Number,
    default: 80 // Default max length for summary display
  }
});

// --- Emits ---
const emit = defineEmits(['edit', 'delete']);

// --- Computed ---
const truncatedSummary = computed(() => {
  if (!props.chapter.summary) return '';
  if (props.chapter.summary.length <= props.summaryMaxLength) {
    return props.chapter.summary;
  }
  return props.chapter.summary.slice(0, props.summaryMaxLength) + '...';
});

// --- Methods ---
const handleEdit = () => {
  emit('edit', props.chapter.id); // 发送章节 ID 给父组件
};

const handleDelete = () => {
  // 可以先在此处弹出确认框，或由父组件处理
  // 例如：if (confirm('确定删除此章节及其所有场景吗？')) { ... }
  emit('delete', props.chapter.id); // 发送章节 ID 给父组件
};

</script>

<style scoped>
.chapter-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  margin-bottom: 8px;
  border: 1px solid #eee;
  border-radius: 4px;
  background-color: #fff;
  transition: box-shadow 0.2s ease-in-out;
}

.chapter-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chapter-info {
  flex-grow: 1;
  margin-right: 15px; /* Space between info and actions */
}

.chapter-title {
  font-weight: bold;
  display: block; /* Ensure title takes its own line if summary is long */
  margin-bottom: 4px;
}

.chapter-summary {
  font-size: 0.9em;
  color: #666;
  margin: 0;
  line-height: 1.4;
}

.chapter-actions {
  display: flex;
  align-items: center;
  gap: 8px; /* Space between buttons */
}

.drag-handle {
  cursor: grab;
  color: #ccc;
  margin-left: 10px;
}
.drag-handle:active {
    cursor: grabbing;
}
</style>