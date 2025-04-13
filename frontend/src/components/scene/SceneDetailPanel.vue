<template>
  <div class="scene-detail-panel" v-loading="isLoadingOverall" element-loading-text="加载场景数据...">
    <!-- 错误提示 -->
    <el-alert v-if="sceneStore.error" :title="`加载或操作场景时出错: ${sceneStore.error}`" type="error" show-icon
              closable @close="sceneStore._setError('details', null)"/>
    <el-alert v-if="sceneStore.generationError" :title="`内容生成时出错: ${sceneStore.generationError}`" type="warning"
              show-icon closable @close="sceneStore._setError('generating', null)"/>

    <div v-if="sceneStore.activeScene && !sceneStore.isLoadingDetails">
      <!-- 操作按钮区域 (替代 PageHeader 的 extra) -->
      <div class="panel-actions">
        <el-button
            type="primary"
            @click="triggerRAGGeneration"
            :loading="sceneStore.isGenerating"
            :disabled="sceneStore.isLoadingDetails || !sceneStore.activeScene.goal"
            size="small"
            :icon="MagicStick"
        >
          {{ sceneStore.isGenerating ? '生成中...' : '生成场景内容' }}
        </el-button>
        <el-button
            type="danger"
            @click="confirmDeleteScene"
            :disabled="!sceneStore.activeScene || sceneStore.isLoadingDetails || sceneStore.isGenerating"
            :icon="Delete"
            plain
            size="small"
        >
          删除场景
        </el-button>
        <el-button @click="$emit('close')" :icon="Close" size="small">关闭</el-button>
      </div>

      <el-tabs v-model="activeTab" tab-position="top">
        <el-tab-pane label="场景元数据" name="metadata">
          <el-card class="box-card metadata-card" shadow="never">
            <SceneMetadataForm
                :scene="sceneStore.activeScene"
                :loading="sceneStore.isLoadingDetails"
                :project-id="sceneStore.activeScene.project_id"
                @save="handleMetadataUpdated"
            />
          </el-card>
        </el-tab-pane>
        <el-tab-pane label="场景内容" name="content">
          <SceneContentDisplay
              style="height: calc(75vh - 100px);"
              :content="localSceneContent"
              :loading="sceneStore.isLoadingDetails || sceneStore.isGenerating"
              :read-only="false"
              @update-content="handleContentChange"
              @save-content="saveContentChanges"
              class="content-display-card"
          />
          <div v-if="contentHasChanged && activeTab === 'content'" class="save-content-bar">
            <el-text type="warning" size="small">内容已修改，请记得保存。</el-text>
          </div>
        </el-tab-pane>

      </el-tabs>

    </div>
    <el-empty v-else-if="!sceneStore.isLoadingDetails" description="未找到场景或场景加载失败"></el-empty>

  </div>
</template>

<script setup>
import {ref, computed, onMounted, watch, provide, defineProps, defineEmits} from 'vue';
// 移除 useRouter 和 useRoute，因为不再是独立页面
import {useSceneStore} from '@/store/scene';
// Project store 可能仍需要，比如获取 projectId
import {useProjectStore} from '@/store/project';
import SceneMetadataForm from '@/components/scene/SceneMetadataForm.vue';
import SceneContentDisplay from '@/components/scene/SceneContentDisplay.vue';
import {
  ElMessage,
  ElMessageBox,
  ElAlert,
  ElButton,
  ElCard,
  ElEmpty,
  ElIcon,
  ElTabs,
  ElTabPane,
  ElText
} from 'element-plus';
import {Delete, MagicStick, Close, DocumentChecked} from '@element-plus/icons-vue';

// --- 组件 Props 和 Emits ---
const props = defineProps({
  sceneId: {
    type: Number,
    required: true,
  },
});

const emit = defineEmits(['close', 'scene-deleted', 'scene-updated']); // 定义发出的事件

// --- Stores ---
const sceneStore = useSceneStore();
const projectStore = useProjectStore(); // 假设 projectId 仍可从 projectStore 获取

// --- State ---
const localSceneContent = ref(''); // 本地存储编辑器内容
const contentHasChanged = ref(false); // 标记内容是否被用户编辑过
const isSavingContent = ref(false); // 标记内容保存状态
const activeTab = ref('metadata'); // 控制显示内容或元数据

// --- Computed ---
const isLoadingOverall = computed(() => sceneStore.isLoadingDetails); // 主加载状态

// --- Methods ---
const fetchData = async () => {
  if (props.sceneId) {
    await sceneStore.fetchSceneDetails(props.sceneId);
    // 确保 activeScene 更新后再设置本地内容
    if (sceneStore.activeScene) {
      localSceneContent.value = sceneStore.activeScene.generated_content || '';
    } else {
      localSceneContent.value = ''; // 场景加载失败或不存在
    }
    contentHasChanged.value = false; // 重置更改标记
    activeTab.value = 'metadata'; // 默认显示内容 Tab
  } else {
    // 理论上不应该发生，因为 prop 是 required 的
    console.error('SceneDetailPanel: 无效的 sceneId prop');
  }
};

const triggerRAGGeneration = async () => {
  if (!props.sceneId) return;
  try {
    await ElMessageBox.confirm(
        '这将使用 AI 生成新的场景内容，可能会覆盖现有未保存的修改。是否继续？',
        '确认生成',
        {confirmButtonText: '生成', cancelButtonText: '取消', type: 'warning'}
    );
  } catch {
    return; // 用户取消
  }

  try {
    await sceneStore.generateSceneContent(props.sceneId);
    ElMessage.success('场景内容生成成功！');
    // 生成后，store 中的 activeScene 会更新，需要重新同步到本地
    if (sceneStore.activeScene) {
      localSceneContent.value = sceneStore.activeScene.generated_content || '';
    }
    contentHasChanged.value = false; // 生成后视为未更改状态
  } catch (err) {
    console.error('RAG generation failed:', err);
    // 错误消息由 store 处理并在 Alert 中显示
  }
};

const confirmDeleteScene = async () => {
  if (!props.sceneId) return;
  try {
    const deletedId = props.sceneId; // 记录ID
    await sceneStore.deleteScene(deletedId);
    ElMessage.success('场景已删除');
    emit('scene-deleted', deletedId); // 通知父组件场景已被删除
    emit('close'); // 删除后关闭详情面板

  } catch (err) {
    if (err !== 'cancel') {
      console.error('删除场景失败:', err);
      // 错误消息由 store 处理并在 Alert 中显示
    }
  }
};

// 处理元数据表单的 'updated' 事件
const handleMetadataUpdated = async (formData) => {
  if (!props.sceneId) return;
  isSavingContent.value = true;
  try {
    const updateData = {
       title: formData.data.title,
       goal: formData.data.goal,
       summary: formData.data.summary,
       status: formData.data.status,
       chapter_id: formData.data.chapter_id === '' ? null : formData.data.chapter_id, // 处理空字符串情况
       order_in_chapter: formData.data.order_in_chapter,
    };

    // // 调用 store action 更新场景
    await sceneStore.updateScene(formData.id, updateData);

    ElMessage.success('内容修改已保存');
    contentHasChanged.value = false; // 重置标记
    emit('scene-save', props.sceneId); // 通知父组件内容已更新
  } catch (err) {
    console.error("保存内容更改失败:", err);
    // 错误消息由 store 处理并在 Alert 中显示
  } finally {
    isSavingContent.value = false;
  }
  // ElMessage.success('场景元数据已保存。');
  // emit('scene-save', props.sceneId); // 通知父组件元数据已更新
  // 如果元数据变化影响内容，可以提示用户重新生成
  if (contentHasChanged.value) {
    ElMessage.info('元数据已更新。如果修改了关键信息，可能需要重新生成或调整场景内容。');
  }
};

// 处理内容显示/编辑器组件发出的内容更新事件
const handleContentChange = (newContent) => {
  // 此处可用于调试或额外逻辑
  localSceneContent.value = newContent;
  contentHasChanged.value = true;
  console.log("内容编辑中...");
};

// 保存内容修改
const saveContentChanges = async () => {
  if (!props.sceneId || !contentHasChanged.value || isSavingContent.value) return;
  isSavingContent.value = true;
  try {
    await sceneStore.updateScene(props.sceneId, {
      generated_content: localSceneContent.value // 保存本地编辑的内容
    });
    ElMessage.success('内容修改已保存');
    contentHasChanged.value = false; // 重置标记
    emit('scene-save', props.sceneId); // 通知父组件内容已更新
  } catch (err) {
    console.error("保存内容更改失败:", err);
    // 错误消息由 store 处理并在 Alert 中显示
  } finally {
    isSavingContent.value = false;
  }
};

// --- Lifecycle Hooks ---
onMounted(() => {
  fetchData();
});

// --- Watchers ---
// 监听 prop sceneId 的变化，以便在父组件切换场景时重新加载数据
watch(() => props.sceneId, (newId, oldId) => {
  if (newId !== oldId && newId) {
    fetchData();
  }
});

// 当组件实例被卸载时，清理活动场景状态（如果需要的话）
// 注意：activeScene 现在由 sceneStore 管理，不一定需要在此清理，
// 取决于 StructureEditor 是否在切换视图时清理或依赖 sceneStore 的管理。
// 暂时移除 onUnmounted 清理，让 sceneStore 管理 activeScene
/*
import { onUnmounted } from 'vue';
onUnmounted(() => {
  // 可能不需要清理，因为父组件会控制显示哪个场景
  // sceneStore.clearActiveScene();
});
*/

// --- Provide/Inject (可选) ---
// 如果子组件如 SceneMetadataForm 仍需 sceneId，可以通过 provide/inject
provide('sceneId', computed(() => props.sceneId));

</script>

<style scoped>
.scene-detail-panel {
  padding: 0px 15px 15px 15px; /* 调整内边距，顶部不需要，因为会被卡片header覆盖 */
  height: 100%; /* 确保面板填满容器 */
  display: flex;
  flex-direction: column;
}

.panel-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding-bottom: 10px;
  margin-bottom: 10px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.panel-actions .el-button {
  margin-left: 8px;
}


.box-card {
  margin-bottom: 0; /* 移除元数据卡片的下边距，因为在 Tab 内 */
  border: none; /* 移除卡片边框，使其融入 Tab */
  box-shadow: none; /* 移除卡片阴影 */
}

.metadata-card {
  padding: 10px; /* 给元数据表单一些内边距 */
}

.content-display-card {
  margin-bottom: 0; /* 移除内容显示区域的下边距 */
  border: 1px solid var(--el-border-color-light); /* 给编辑器一个边框 */
  border-radius: 4px;
}

.save-content-bar {
  /* position: sticky; */ /* 改为非粘性，放在Tab内容底部 */
  /* bottom: 0; */
  width: 100%;
  background-color: var(--el-color-warning-light-9); /* 淡黄色背景 */
  padding: 8px 15px;
  border-top: 1px solid var(--el-color-warning-light-5);
  /* box-shadow: 0 -1px 3px rgba(0, 0, 0, 0.05); */
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-top: 10px; /* 与上方编辑器隔开 */
  border-radius: 4px;
}

.el-tabs {
  flex-grow: 1; /* 让 Tabs 占据剩余空间 */
}

:deep(.el-tabs__content) {
  flex-grow: 1; /* 让 Tab 内容区域占据空间 */
  overflow-y: auto; /* 如果内容超长，允许滚动 */
}

:deep(.el-tab-pane) {
  height: 100%; /* 确保 Tab Pane 填满内容区域 */
  display: flex; /* 允许内部元素更好地布局 */
  flex-direction: column;
}

</style>