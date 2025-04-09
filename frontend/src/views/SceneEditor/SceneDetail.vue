<template>
  <div class="scene-detail-view" v-loading="isLoadingOverall" element-loading-text="加载场景数据...">
    <el-page-header @back="goBack" :content="pageTitle" class="page-header">
       <template #extra>
         <div class="header-actions">
             <el-button
               type="danger"
               @click="confirmDeleteScene"
               :disabled="!sceneStore.activeScene || sceneStore.isLoadingDetails || sceneStore.isGenerating"
               :icon="Delete"
               plain
             >
               删除场景
             </el-button>
          </div>
       </template>
    </el-page-header>

    <el-alert v-if="sceneStore.error" :title="`加载或操作场景时出错: ${sceneStore.error}`" type="error" show-icon closable @close="sceneStore._setError('details', null)"/>
    <el-alert v-if="sceneStore.generationError" :title="`内容生成时出错: ${sceneStore.generationError}`" type="warning" show-icon closable @close="sceneStore._setError('generating', null)"/>

    <div v-if="sceneStore.activeScene && !sceneStore.isLoadingDetails">
      <el-row :gutter="20">
        <el-col :span="24">
          <el-card class="box-card metadata-card">
            <template #header>
              <div class="card-header">
                <span>场景元数据</span>
              </div>
            </template>
            <SceneMetadataForm
              :scene="sceneStore.activeScene"
              :loading="sceneStore.isLoadingDetails"
              :project-id="sceneStore.activeScene.project_id"
              @updated="handleMetadataUpdated"
             />
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
           <el-card class="box-card generation-card">
             <template #header>
               <div class="card-header">
                 <span>内容生成 (RAG)</span>
                  <el-button
                    type="primary"
                    @click="triggerRAGGeneration"
                    :loading="sceneStore.isGenerating"
                    :disabled="sceneStore.isLoadingDetails || !sceneStore.activeScene.goal"
                  >
                    <el-icon v-if="!sceneStore.isGenerating"><MagicStick /></el-icon>
                    {{ sceneStore.isGenerating ? '正在生成中...' : '生成场景内容' }}
                  </el-button>
               </div>
             </template>
             <el-text v-if="!sceneStore.activeScene.goal" type="warning" size="small">
                 提示：请先填写并保存“场景目标/核心内容”以启用内容生成功能。
             </el-text>
              <el-text v-else type="info" size="small">
                 点击按钮将根据场景目标、概要、人物、设定等信息，结合 RAG 技术生成场景草稿。
             </el-text>
           </el-card>
        </el-col>
      </el-row>

      <SceneContentDisplay
        :content="sceneContent"
        :loading="sceneStore.isLoadingDetails || sceneStore.isGenerating"
        :read-only="false"
        @update:content="handleContentChange"
        @save-content="saveContentChanges"
        class="content-display-card"
       />
       <!-- 如果内容编辑后需要手动保存 -->
       <div v-if="contentHasChanged" class="save-content-bar">
          <el-text type="warning" size="small">内容已修改，记得保存元数据以保存内容。</el-text>
       </div>

    </div>
    <el-empty v-else-if="!sceneStore.isLoadingDetails" description="未找到场景或场景加载失败"></el-empty>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, provide } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSceneStore } from '@/store/scene';
import { useProjectStore } from '@/store/project'; // 可能需要项目信息
import SceneMetadataForm from '@/components/scene/SceneMetadataForm.vue';
import SceneContentDisplay from '@/components/scene/SceneContentDisplay.vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Delete, MagicStick } from '@element-plus/icons-vue';

// --- Router & Route ---
const route = useRoute();
const router = useRouter();
const sceneId = computed(() => parseInt(route.params.sceneId, 10)); // 从路由参数获取 sceneId

// --- Stores ---
const sceneStore = useSceneStore();
const projectStore = useProjectStore(); // 获取当前项目，可能用于导航返回等

// --- State ---
const localSceneContent = ref(''); // 本地存储编辑器内容
const contentHasChanged = ref(false); // 标记内容是否被用户编辑过
const isSavingContent = ref(false); // 如果有单独的内容保存逻辑

// --- Computed ---
const isLoadingOverall = computed(() => sceneStore.isLoadingDetails); // 主加载状态
const pageTitle = computed(() => {
  if (sceneStore.isLoadingDetails) return '加载中...';
  if (sceneStore.activeScene) return `编辑场景: ${sceneStore.activeScene.title || '未命名场景'}`;
  return '场景详情';
});
// 将 store 中的 generated_content 同步到本地 ref，并允许本地编辑
const sceneContent = computed({
    get: () => sceneStore.activeScene?.generated_content || '',
    set: (value) => {
        localSceneContent.value = value; // 更新本地 ref
        if (value !== (sceneStore.activeScene?.generated_content || '')) {
            contentHasChanged.value = true; // 标记内容已更改
        }
    }
});

// --- Methods ---
const fetchData = async () => {
  if (sceneId.value) {
    await sceneStore.fetchSceneDetails(sceneId.value);
    // 初始化本地内容 ref
    localSceneContent.value = sceneStore.activeScene?.generated_content || '';
    contentHasChanged.value = false; // 重置更改标记
  } else {
    ElMessage.error('无效的场景 ID');
    router.push({ name: 'ProjectDashboard' }); // 或者跳转到项目工作区
  }
};

const goBack = () => {
  // 导航回项目的故事结构页面，需要当前项目的 ID
  if (projectStore.currentProject?.id) {
      router.push({ name: 'StructureEditor', params: { projectId: projectStore.currentProject.id } });
  } else {
      router.push({ name: 'ProjectDashboard' }); // Fallback
  }
};

const triggerRAGGeneration = async () => {
    if (!sceneId.value) return;
    try {
        await ElMessageBox.confirm(
            '这将使用 AI 生成新的场景内容，可能会覆盖现有内容。是否继续？',
            '确认生成',
            { confirmButtonText: '生成', cancelButtonText: '取消', type: 'warning' }
        );
    } catch {
        return; // 用户取消
    }

    try {
        await sceneStore.generateSceneContent(sceneId.value);
        ElMessage.success('场景内容生成成功！');
        // 生成后，store 中的 activeScene 会更新，计算属性 sceneContent 会自动反映
        localSceneContent.value = sceneStore.activeScene?.generated_content || ''; // 确保本地也同步
        contentHasChanged.value = false; // 生成后视为未更改状态
    } catch (err) {
        // 错误信息已在 store 中设置，并会显示在 Alert 中
        console.error('RAG generation failed:', err);
        // ElMessage.error(`生成失败: ${sceneStore.generationError || '请稍后重试'}`);
    }
};

const confirmDeleteScene = async () => {
  if (!sceneId.value) return;
  try {
    await ElMessageBox.confirm(
      `确定要永久删除场景 "${sceneStore.activeScene?.title || '此场景'}" 吗？此操作无法撤销。`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    );

    await sceneStore.deleteScene(sceneId.value);
    ElMessage.success('场景已删除');
    goBack(); // 删除成功后返回列表页

  } catch (err) {
      if (err !== 'cancel') { // 用户点击了取消以外的操作
        console.error('删除场景失败:', err);
        // ElMessage.error(`删除失败: ${sceneStore.error || '请稍后重试'}`);
      }
  }
};

// 处理元数据表单的 'updated' 事件
const handleMetadataUpdated = () => {
  // 元数据保存成功后，如果内容也被修改过，可以选择在这里一并“认为”内容也被保存了
  // 或者提示用户 RAG 生成的内容需要重新生成（如果元数据变化影响内容的话）
  if (contentHasChanged.value) {
      ElMessage.info('场景元数据已保存。如果修改了影响生成内容的关键信息（如目标），建议重新生成内容。');
      // 如果你的后端 updateScene API 同时接受 generated_content，可以在 SceneMetadataForm 的 submit 中处理
      // 这里假设内容需要通过 RAG 生成，或者元数据保存不直接关联内容保存
  }
};

// 处理内容显示/编辑器组件发出的内容更新事件
const handleContentChange = (newContent) => {
    // 这个函数理论上由 computed sceneContent 的 setter 处理了
    // 但如果 SceneContentDisplay 使用不同的事件机制，可以在这里更新 localSceneContent 和 contentHasChanged
    localSceneContent.value = newContent;
    contentHasChanged.value = true;
    console.log("Content changed in editor:", newContent);
};

// 如果需要单独保存内容修改（不推荐，最好随元数据一起保存）

const saveContentChanges = async () => {
    if (!sceneId.value || !contentHasChanged.value) return;
    isSavingContent.value = true;
    try {
        await sceneStore.updateScene(sceneId.value, {
            generated_content: localSceneContent.value
        });
        ElMessage.success('内容修改已保存');
        contentHasChanged.value = false; // 重置标记
    } catch (err) {
        console.error("Failed to save content changes:", err);
        ElMessage.error(`保存内容失败: ${sceneStore.error || '未知错误'}`);
    } finally {
        isSavingContent.value = false;
    }
};


// --- Lifecycle Hooks ---
onMounted(() => {
  fetchData();
});

// 监听路由参数变化，以便在同一组件内导航到不同场景时重新加载数据
watch(sceneId, (newId, oldId) => {
  if (newId !== oldId && newId) {
    fetchData();
  }
});

// 当组件卸载时，清理活动场景状态（可选，取决于你的全局状态管理策略）
import { onUnmounted } from 'vue';
onUnmounted(() => {
  sceneStore.clearActiveScene();
});

// --- Provide/Inject (可选) ---
// 如果子组件需要频繁访问 sceneId，可以 provide 它
provide('sceneId', sceneId);

</script>

<style scoped>
.scene-detail-view {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.header-actions {
    display: flex;
    align-items: center;
}

.box-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metadata-card, .generation-card, .content-display-card {
    margin-bottom: 20px; /* 保持卡片间距 */
}

.save-content-bar {
    position: sticky;
    bottom: 0;
    left: 0; /* 或者根据你的布局调整 */
    width: 100%; /* 或者适应父容器宽度 */
    background-color: rgba(255, 255, 255, 0.9);
    padding: 10px 20px;
    border-top: 1px solid var(--el-border-color-lighter);
    box-shadow: 0 -2px 5px rgba(0,0,0,0.1);
    display: flex;
    justify-content: flex-end; /* 或 center / space-between */
    align-items: center;
    z-index: 10; /* 确保在其他内容之上 */
}
.save-content-bar .el-text {
    margin-right: 15px;
}

</style>