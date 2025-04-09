<template>
  <el-card shadow="hover" class="scene-item" :data-scene-id="scene.id" :body-style="{ padding: '10px' }">
    <div class="scene-content">
      <span class="scene-title" @click="goToSceneDetail">{{ scene.title || '未命名场景' }}</span>
      <el-tag size="small" :type="statusType" class="scene-status">
        {{ statusText }}
      </el-tag>
    </div>
    <!-- 可选：添加拖拽句柄 -->
    <!-- <span class="drag-handle">☰</span> -->
  </el-card>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { computed } from 'vue';
import {ElMessage} from "element-plus";

// --- Props ---
const props = defineProps({
  scene: {
    type: Object,
    required: true, // 期望接收 SceneReadMinimal 或类似结构
  },
});

// --- Router ---
const router = useRouter();

// --- Methods ---
const goToSceneDetail = () => {
  if (props.scene && props.scene.id) {
    router.push({ name: 'SceneDetail', params: { sceneId: props.scene.id } }); // 确保路由名称 'SceneDetail' 正确
  } else {
    console.error('无法导航：场景 ID 无效');
    ElMessage.error('无法导航到场景详情，ID 无效');
  }
};

// --- Computed ---
// 将场景状态映射为 Element Plus Tag 的类型
const statusType = computed(() => {
  switch (props.scene?.status) {
    case 'PLANNED': return 'info';
    case 'DRAFTED': return ''; // default
    case 'REVISING': return 'warning';
    case 'COMPLETED': return 'success';
    case 'GENERATING': return 'primary'; // 假设有生成中状态
    case 'GENERATION_FAILED': return 'danger'; // 假设有生成失败状态
    default: return 'info';
  }
});

// 将场景状态映射为可读文本 (假设后端返回的是枚举字符串)
const statusText = computed(() => {
   // 你可能需要一个更完善的映射表或从后端获取本地化文本
  const statusMap = {
    PLANNED: '计划中',
    DRAFTED: '草稿',
    REVISING: '修订中',
    COMPLETED: '已完成',
    GENERATING: '生成中',
    GENERATION_FAILED: '生成失败',
  };
  return statusMap[props.scene?.status] || props.scene?.status || '未知状态';
});

</script>

<style scoped>
.scene-item {
  margin-bottom: 8px;
  cursor: grab; /* 指示可拖拽 */
  transition: background-color 0.2s ease;
}
.scene-item:hover {
  background-color: #f5f7fa;
}
.scene-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.scene-title {
  flex-grow: 1;
  margin-right: 10px;
  cursor: pointer; /* 指示可点击 */
  color: var(--el-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.scene-title:hover {
  text-decoration: underline;
}
.scene-status {
  flex-shrink: 0;
}
/* 可选的拖拽句柄样式 */
/*
.drag-handle {
  cursor: move;
  margin-right: 8px;
  color: #909399;
}
*/
</style>