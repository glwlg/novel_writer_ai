<template>
  <el-card shadow="hover" class="character-card">
    <template #header>
      <div class="card-header">
        <span>{{ character.name }}</span>
        <div>
          <el-tooltip content="编辑角色" placement="top">
            <el-button circle :icon="Edit" size="small" @click="emitEdit" />
          </el-tooltip>
           <el-tooltip content="删除角色" placement="top">
            <el-button type="danger" circle :icon="Delete" size="small" @click="emitDelete" />
          </el-tooltip>
        </div>
      </div>
    </template>

    <div class="card-content">
       <p v-if="character.description" class="description">
          {{ truncateText(character.description, 100) }}
       </p>
       <el-tag v-if="character.current_status" size="small" type="info" effect="light" style="margin-top: 5px;">
          状态：{{ character.current_status }}
       </el-tag>
       <p v-else-if="!character.description" class="no-description">
            暂无描述。
       </p>
    </div>

    <template #footer>
        <small>创建于：{{ formattedDate(character.created_at) }}</small>
    </template>
  </el-card>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';
import { ElCard, ElButton, ElTooltip, ElTag } from 'element-plus';
import { Edit, Delete } from '@element-plus/icons-vue';
import {format} from "date-fns";
// 可选的日期格式化库
// import { format } from 'date-fns';

const props = defineProps({
  character: {
    type: Object,
    required: true,
    // 对预期字段进行基本验证
    validator: (value) => {
        return value && typeof value.id === 'number' && typeof value.name === 'string';
    }
  }
});

const emit = defineEmits(['edit', 'delete']);

const emitEdit = () => {
  emit('edit', props.character); // 发送整个角色对象，方便父组件使用
};

const emitDelete = () => {
  emit('delete', props.character.id); // 只发送 ID 用于删除
};

// 辅助函数：截断长文本
const truncateText = (text, maxLength) => {
  if (!text) return '';
  if (text.length <= maxLength) {
    return text;
  }
  return text.substring(0, maxLength) + '...';
};

// 可选：日期格式化函数
const formattedDate = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    // 根据需要调整日期格式
    return format(new Date(dateString), 'yyyy-MM-dd HH:mm');
  } catch (e) {
    console.error("格式化日期时出错:", e);
    return dateString; // 出错时回退到原始字符串
  }
};
</script>

<style scoped>
.character-card {
  height: 100%; /* 让同一行的卡片可能等高 */
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header span {
    font-weight: bold;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin-right: 10px; /* 在名字和按钮之间添加间距 */
}

.card-content {
    flex-grow: 1; /* 允许内容区域扩展 */
    font-size: 0.9em;
    color: var(--el-text-color-regular);
    line-height: 1.4;
}

.description {
    margin-bottom: 10px;
    /* 如果希望保留描述中的换行符，可以添加 white-space: pre-wrap; */
    white-space: pre-wrap;
    word-break: break-word; /* 防止长单词溢出 */
}
.no-description {
    color: var(--el-text-color-secondary);
    font-style: italic;
}
</style>