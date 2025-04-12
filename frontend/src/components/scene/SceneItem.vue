<template>
  <el-card shadow="hover" class="scene-item" :data-scene-id="scene.id" :body-style="{ padding: '10px' }">
    <div class="scene-content">
      <span class="scene-title" @click="goToSceneDetail">{{
          scene.title || '未命名场景'
        }}</span>
      <el-tag size="small" :type="statusType" class="scene-status">
        {{ statusText }}
      </el-tag>
      <el-popconfirm
          title="这将使用 AI 生成新的场景内容，可能会覆盖现有内容。是否继续？"
          confirm-button-text="生成"
          cancel-button-text="取消"
          @confirm="triggerRAGGeneration"
          width="250"
      >
        <template #reference>
          <el-button link type="success" :icon="MagicStick" @click.stop size="default"
                     title="生成内容"></el-button>
        </template>
      </el-popconfirm>
      <el-popconfirm
          title="确定删除此场景吗？"
          confirm-button-text="确认删除"
          cancel-button-text="取消"
          @confirm="confirmDeleteScene"
          width="250"
      >
        <template #reference>
          <el-button link type="danger" :icon="Delete" @click.stop size="default"
                     title="删除场景"></el-button>
        </template>
      </el-popconfirm>
    </div>
    <!-- 可选：添加拖拽句柄 -->
    <!-- <span class="drag-handle">☰</span> -->
  </el-card>
</template>

<script setup>
import {useRouter} from 'vue-router';
import {computed, defineEmits} from 'vue';
import {ElMessage, ElMessageBox, ElPopconfirm} from "element-plus";
import {Delete, MagicStick} from "@element-plus/icons-vue";
import {useSceneStore} from "@/store/index.js";
// --- Stores ---
const sceneStore = useSceneStore();
// --- Props ---
const props = defineProps({
  scene: {
    type: Object,
    required: true, // 期望接收 SceneReadMinimal 或类似结构
  },
});

// --- Router ---
const router = useRouter();
const emit = defineEmits(['generate']);
// --- Methods ---
const goToSceneDetail = () => {
  if (props.scene && props.scene.id) {
    router.push({name: 'SceneDetail', params: {sceneId: props.scene.id}}); // 确保路由名称 'SceneDetail' 正确
  } else {
    console.error('无法导航：场景 ID 无效');
    ElMessage.error('无法导航到场景详情，ID 无效');
  }
};

// --- Computed ---
// 将场景状态映射为 Element Plus Tag 的类型
const statusType = computed(() => {
  switch (props.scene?.status) {
    case 'PLANNED':
      return 'info';
    case 'DRAFTED':
      return 'info';
    case 'REVISING':
      return 'warning';
    case 'COMPLETED':
      return 'success';
    case 'GENERATING':
      return 'primary';
    case 'GENERATION_FAILED':
      return 'danger';
    default:
      return 'info';
  }
});
const triggerRAGGeneration = async () => {
  emit('generate', props.scene.id); // Emit chapter ID for scene generation
};
const confirmDeleteScene = async () => {
  if (!props.scene.id) return;
  try {
    await ElMessageBox.confirm(
        `确定要永久删除场景 "${props.scene?.title || '此场景'}" 吗？此操作无法撤销。`,
        '确认删除',
        {confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning'}
    );

    await sceneStore.deleteScene(props.scene.id);
    ElMessage.success('场景已删除');

  } catch (err) {
    if (err !== 'cancel') { // 用户点击了取消以外的操作
      console.error('删除场景失败:', err);
      // ElMessage.error(`删除失败: ${sceneStore.error || '请稍后重试'}`);
    }
  }
};

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