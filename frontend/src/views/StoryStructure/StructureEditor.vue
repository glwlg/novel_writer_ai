<template>
  <div class="structure-editor-view" v-loading="isLoadingOverall" element-loading-text="加载中...">
    <!-- 1. 修改 Page Header -->
    <el-page-header @back="goBackToProject" :content="pageTitle" class="page-header">
      <template #extra>
        <el-button type="primary" @click="openCreateVolumeDialog" :icon="Plus">新建卷</el-button>
        <!-- 新建章节按钮移到卷内部或保留在这里，但需要选择卷 -->
        <!-- <el-button type="success" @click="openCreateChapterDialog()" :icon="Plus">新建章节</el-button> -->
        <!-- 移除了“新建未分配场景”按钮 -->
      </template>
    </el-page-header>

    <el-alert v-if="volumeStore.error || chapterStore.error || sceneStore.error"
              :title="`加载数据时出错: ${volumeStore.error || chapterStore.error || sceneStore.error}`" type="error"
              show-icon closable
              @close="clearErrors"/>

    <!-- 2. 修改布局，移除右侧列，左侧占满 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <!-- 3. 使用 Collapse 或类似结构展示卷和章节 -->
        <div v-if="volumesWithChapters.length === 0 && !isLoadingOverall" class="empty-list">
          <el-empty description="还没有创建任何卷，点击右上角“新建卷”开始吧！"></el-empty>
        </div>
        <el-collapse v-model="activeVolumeIds" v-else class="volume-list">
          <el-collapse-item v-for="volume in sortedVolumesWithChapters" :key="volume.id" :name="volume.id.toString()">
            <template #title>
              <div class="volume-header">
                <span class="volume-title">{{ volume.title || '未命名卷' }}</span>
                <div class="volume-actions">
                  <el-button link type="primary" :icon="Edit" @click.stop="openEditVolumeDialog(volume)" size="default"
                             title="编辑卷信息"></el-button>
                  <el-button link type="success" :icon="Plus" @click.stop="openCreateChapterDialog(volume.id)"
                             size="default" title="在本卷新建章节"></el-button>
                  <el-popconfirm
                      title="确定删除此卷吗？卷下的所有章节和场景都将被删除！"
                      confirm-button-text="确认删除"
                      cancel-button-text="取消"
                      @confirm="confirmDeleteVolume(volume)"
                      width="250"
                  >
                    <template #reference>
                      <el-button link type="danger" :icon="Delete" @click.stop size="default"
                                 title="删除卷"></el-button>
                    </template>
                  </el-popconfirm>
                </div>
              </div>
            </template>

            <!-- 章节列表 -->
            <div v-if="volume.chapters.length === 0" class="empty-list inside-volume">
              <el-empty description="该卷下还没有章节" :image-size="60"></el-empty>
            </div>
            <div v-else class="chapter-list-in-volume">
              <ChapterItem
                  v-for="chapter in sortedChapters(volume.chapters)"
                  :key="chapter.id"
                  :chapter="chapter"
                  :is-selected="selectedChapterId === chapter.id"
                  @select="selectChapter"
                  @edit="openEditChapterDialog"
                  @delete="confirmDeleteChapter"
                  @generate="triggerScenesGeneration"
                  @view="openChapterDialog"
              />
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-col>
      <!-- 移除了右侧未分配场景列 -->
    </el-row>

    <!-- 对话框：创建/编辑卷 -->
    <el-dialog v-model="volumeDialogVisible" :title="isEditingVolume ? '编辑卷' : '新建卷'" width="500px"
               @closed="resetVolumeForm">
      <el-form ref="volumeFormRef" :model="volumeFormData" :rules="volumeFormRules" label-position="top">
        <el-form-item label="卷名" prop="title">
          <el-input v-model="volumeFormData.title" placeholder="请输入卷名"/>
        </el-form-item>
        <el-form-item label="卷概要" prop="summary">
          <el-input v-model="volumeFormData.summary" type="textarea" :rows="3" placeholder="（可选）输入卷的概要"/>
        </el-form-item>
        <el-form-item label="排序权重" prop="order">
          <el-input-number v-model="volumeFormData.order" :min="0" controls-position="right"/>
          <el-text size="small" type="info" style="margin-left: 10px;">数字越小越靠前</el-text>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="volumeDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveVolume" :loading="isSavingVolume">
            {{ isEditingVolume ? '保存修改' : '创建卷' }}
          </el-button>
        </span>
      </template>
    </el-dialog>


    <!-- 对话框：创建/编辑章节 (增加卷选择) -->
    <el-dialog v-model="chapterDialogVisible" :title="isEditingChapter ? '编辑章节' : '新建章节'" width="500px"
               @closed="resetChapterForm">
      <ChapterForm project-id="{{ projectStore.currentProject?.id }}" :initial-data="chapterFormData"
                   :is-editing="isEditingChapter"
                   @save="saveChapter"
                   @cancel="chapterDialogVisible = false"/>
    </el-dialog>

    <!-- 移除了创建场景对话框 -->

    <!-- 对话框：小说内容 (保持不变) -->
    <el-dialog v-model="chapterContentDialogVisible" :title="chapterStore.activeChapter?.title" width="60vw"
               @closed="()=>{/* 可选：关闭时重置什么 */}">
      <div v-if="isCreatingChapterContent" class="content-loading">
        <el-skeleton :rows="5" animated/>
      </div>
      <div v-else>
        <RichTextEditor
            v-if="chapterStore.activeChapter"
            v-model="chapterStore.activeChapter.content"
            :editorProps="{
              attributes: {
                class: 'prose prose-sm sm:prose lg:prose-lg xl:prose-2xl m-5 focus:outline-none',
              },
            }"
        />
        <div v-else>无法加载章节内容</div>
      </div>
      <template #footer>
         <span class="dialog-footer">
           <el-button :loading="isCreatingChapterContent" @click="chapterContentDialogVisible = false">关闭</el-button>
           <el-button type="primary" @click="triggerContentGeneration" :loading="isCreatingChapterContent">
              <el-icon><MagicStick/></el-icon>
             内容优化/生成
           </el-button>
         </span>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import {computed, nextTick, onMounted, ref, watch} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import {useVolumeStore} from '@/store/volume';
import {useChapterStore} from '@/store/chapter';
import {useSceneStore} from '@/store/scene';
import {useProjectStore} from '@/store/project';
import ChapterItem from '@/components/chapter/ChapterItem.vue';
import {ElMessage, ElMessageBox, ElPopconfirm} from 'element-plus';
import {Delete, Document, Edit, MagicStick, Plus} from '@element-plus/icons-vue';
import RichTextEditor from "@/components/common/RichTextEditor.vue";
import ChapterForm from "@/components/chapter/ChapterForm.vue";

// --- Router & Route ---
const route = useRoute();
const router = useRouter();
const projectId = computed(() => parseInt(route.params.projectId, 10));

// --- Stores ---
const volumeStore = useVolumeStore(); // 新增
const chapterStore = useChapterStore();
const sceneStore = useSceneStore();
const projectStore = useProjectStore();

// --- State ---
const selectedChapterId = ref(null);
const activeVolumeIds = ref([]); // 用于 el-collapse 展开状态

// Volume State
const volumeDialogVisible = ref(false);
const isEditingVolume = ref(false);
const volumeFormData = ref({id: null, title: '', summary: '', order: 0});
const volumeFormRef = ref(null);
const isSavingVolume = ref(false);

// Chapter State
const chapterDialogVisible = ref(false);
const isEditingChapter = ref(false);
// 章节表单数据增加 volume_id
const chapterFormData = ref({id: null, volume_id: null, title: '', summary: '', order: 0});
const isSavingChapter = ref(false);

// Chapter Content State (Keep unchanged)
const chapterContentDialogVisible = ref(false);
const isCreatingChapterContent = ref(false);

// Refs for Popconfirm
const chapterDeleteConfirmRef = ref(null);
const chapterDeleteTriggerRef = ref(null);
const chapterToDelete = ref(null); // Store the chapter temporarily for the popconfirm

// --- Computed ---
// 修改 isLoadingOverall 以包含 volumeStore
const isLoadingOverall = computed(() => volumeStore.isLoading || chapterStore.isLoading);
const pageTitle = computed(() => projectStore.currentProject ? `${projectStore.currentProject.title} - 故事结构` : '故事结构');

// 从 store 获取数据
const volumes = computed(() => volumeStore.volumes);
const chapters = computed(() => chapterStore.chapters);
const scenes = computed(() => sceneStore.scenes);

// 将章节按卷分组
const volumesWithChapters = computed(() => {
  const volumeMap = {};
  volumes.value.forEach(vol => {
    volumeMap[vol.id] = {...vol, chapters: []};
  });

  const chapterMap = {};
  chapters.value.forEach(chap => {
    chapterMap[chap.id] = {...chap, scenes: []};
  });

  scenes.value.forEach(scene => {
    if (chapterMap[scene.chapter_id]) {
      chapterMap[scene.chapter_id].scenes.push({...scene});
    }
  });

  chapters.value.forEach(chap => {
     if (volumeMap[chap.volume_id]) {
         volumeMap[chap.volume_id].chapters.push({...chap});
     }
  });

  return Object.values(volumeMap);
});

// 用于排序的计算属性 (按 order 字段)
const sortedVolumesWithChapters = computed(() => {
  return [...volumesWithChapters.value].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
});

const sortedChapters = (chapterArray) => {
  return [...(chapterArray || [])].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
};


// 表单规则
const volumeFormRules = ref({
  title: [{required: true, message: '卷名不能为空', trigger: 'blur'}],
  // summary 和 order 不是必填
});
// 移除 sceneFormRules


// --- Methods ---
const fetchData = async () => {
  if (!projectId.value) {
    ElMessage.error('无效的项目 ID');
    router.push({name: 'ProjectDashboard'});
    return;
  }
  // 总是尝试加载项目详情，它内部可能会触发其他加载
  try {
    await projectStore.fetchProjectDetails(projectId.value); // 确保项目信息加载
    // 并行加载卷和章节
    await Promise.all([
      volumeStore.fetchVolumes(projectId.value),
      chapterStore.fetchChapters(projectId.value),
      sceneStore.fetchScenes(projectId.value)
    ]);
    // 默认展开第一个卷（如果存在）
    if (sortedVolumesWithChapters.value.length > 0) {
      activeVolumeIds.value = [sortedVolumesWithChapters.value[0].id.toString()];
    } else {
      activeVolumeIds.value = [];
    }
  } catch (error) {
    console.error("Error fetching data:", error);
    // 错误已在 store 中处理并显示在 alert 中
  } finally {
    // 初始时不选中任何章节
    selectedChapterId.value = null;
  }
};


const clearErrors = () => {
  volumeStore._setError(null);
  chapterStore._setError(null);
  sceneStore._setError('details', null); // 假设 scene store 还有其他错误类型
};

const goBackToProject = () => {
  // ... (保持不变)
  if (projectId.value) {
    // router.push({name: 'ProjectWorkspace', params: {projectId: projectId.value}});
    router.push({name: 'ProjectDashboard'});
  } else {
    router.push({name: 'ProjectDashboard'});
  }
};

// --- Volume CRUD ---
const openCreateVolumeDialog = () => {
  isEditingVolume.value = false;
  const maxOrder = volumes.value.reduce((max, vol) => Math.max(max, vol.order ?? -1), -1);
  volumeFormData.value = {id: null, title: '', summary: '', order: maxOrder + 1, project_id: projectId.value};
  volumeDialogVisible.value = true;
  nextTick(() => {
    volumeFormRef.value?.clearValidate();
  });
};

const openEditVolumeDialog = (volume) => {
  isEditingVolume.value = true;
  volumeFormData.value = {...volume}; // 浅拷贝编辑
  volumeDialogVisible.value = true;
  nextTick(() => {
    volumeFormRef.value?.clearValidate();
  });
};

const resetVolumeForm = () => {
  volumeFormData.value = {id: null, title: '', summary: '', order: 0};
  volumeFormRef.value?.clearValidate();
};

const saveVolume = async () => {
  if (!volumeFormRef.value) return;
  try {
    await volumeFormRef.value.validate();
    isSavingVolume.value = true;
    const dataToSave = {
      title: volumeFormData.value.title,
      summary: volumeFormData.value.summary,
      order: volumeFormData.value.order,
      project_id: projectId.value // 确保 project_id 传递
    };
    if (isEditingVolume.value) {
      await volumeStore.updateVolume(volumeFormData.value.id, dataToSave);
      ElMessage.success('卷已更新');
    } else {
      await volumeStore.createVolume(projectId.value, dataToSave); // createVolume 应自动处理 project_id
      ElMessage.success('卷已创建');
    }
    volumeDialogVisible.value = false;
  } catch (error) {
    if (error === false) {
      // Validation failed
    } else {
      console.error('保存卷失败:', error);
      // 错误应在 store 中处理
    }
  } finally {
    isSavingVolume.value = false;
  }
};

const confirmDeleteVolume = async (volume) => {
  // 使用 store action 删除，它应该处理卷下章节和场景的级联删除（或给出警告）
  try {
    await volumeStore.deleteVolume(volume.id);
    ElMessage.success(`卷 "${volume.title}" 及内容已删除`);
    // 如果删除的卷是当前展开的，需要处理 activeVolumeIds
    activeVolumeIds.value = activeVolumeIds.value.filter(id => id !== volume.id.toString());
  } catch (error) {
    console.error('删除卷失败:', error);
    // 错误已在 store 中处理
  }
};


// --- Chapter CRUD (Modified) ---
const selectChapter = (chapterId) => {
  selectedChapterId.value = selectedChapterId.value === chapterId ? null : chapterId;
};

const openCreateChapterDialog = (volumeId) => {
  if (!volumeId) {
    ElMessage.warning("请先选择或创建一个卷");
    return;
  }
  isEditingChapter.value = false;
  const parentVolume = volumesWithChapters.value.find(v => v.id === volumeId);
  const maxOrder = parentVolume ? parentVolume.chapters.reduce((max, ch) => Math.max(max, ch.order ?? -1), -1) : -1;
  // 预设 volume_id
  chapterFormData.value = {id: null, volume_id: volumeId, title: '', summary: '', order: maxOrder + 1};
  chapterDialogVisible.value = true;
};

const openEditChapterDialog = (chapter) => {
  isEditingChapter.value = true;
  // 确保 chapter 对象包含 volume_id
  chapterFormData.value = {...chapter};
  chapterDialogVisible.value = true;
};

const resetChapterForm = () => {
  chapterFormData.value = {id: null, volume_id: null, title: '', summary: '', order: 0};
};

const saveChapter = async (saveData) => {
  if (!saveData.data) return;
  try {
    isSavingChapter.value = true;
    const dataToSave = {
      volume_id: saveData.data.volume_id, // 包含 volume_id
      title: saveData.data.title,
      summary: saveData.data.summary,
      order: saveData.data.order,
    };
    if (isEditingChapter.value) {
      await chapterStore.updateChapter(saveData.id, dataToSave);
      ElMessage.success('章节已更新');
    } else {
      // createChapter 需要接收 projectId 和 data (包含 volume_id)
      await chapterStore.createChapter(projectId.value, saveData.data.volume_id, dataToSave);
      ElMessage.success('章节已创建');
    }
    chapterDialogVisible.value = false;
  } catch (error) {
    if (error === false) {
      // Validation failed
    } else {
      console.error('保存章节失败:', error);
    }
  } finally {
    isSavingChapter.value = false;
  }
};

const confirmDeleteChapter = async (chapterId) => {
  if (!chapterId) return;
  const chapter = chapters.value.find(ch => ch.id === chapterId);
  if (!chapter) {
    ElMessage.error("找不到对应的章节");
    return;
  }
  try {
    await chapterStore.deleteChapter(chapterId);
    ElMessage.success(`章节 "${chapter.title}" 及内部场景已删除`);
    if (selectedChapterId.value === chapterId) {
      selectedChapterId.value = null;
    }
  } catch (error) {
    console.error('删除章节失败:', error);
  }
};

// Open Chapter Content Dialog (triggered by @view from ChapterItem)
const openChapterDialog = async (chapterId) => {
  // Fetch the specific chapter data if needed, or use existing store data
  const chapter = chapterStore.chapters.find(ch => ch.id === chapterId);
  if (chapter) {
    // If content might be large or not always loaded, fetch it specifically
    // await chapterStore.fetchChapterDetails(chapterId); // Assuming such an action exists
    chapterStore.setActiveChapter(chapterId); // Use store action to set active chapter
    if (chapterStore.activeChapter) {
      chapterContentDialogVisible.value = true;
    } else {
      ElMessage.error("无法加载章节详细信息");
    }
  } else {
    ElMessage.error("找不到章节信息");
  }
};


// 触发场景生成 (基本不变)
const triggerScenesGeneration = async (chapterId) => {
  if (!chapterId) return;
  const chapter = chapters.value.find(ch => ch.id === chapterId);
  if (!chapter) {
    ElMessage.error("找不到对应的章节");
    return;
  }
  if (chapter.scenes && chapter.scenes.length > 0) {
    try {
      await ElMessageBox.confirm(
          '该章节已存在场景，重新生成将覆盖现有场景。是否继续？',
          '确认覆盖生成',
          {confirmButtonText: '确认生成', cancelButtonText: '取消', type: 'warning'}
      );
    } catch {
      return; // 用户取消
    }
  } else {
    try {
      await ElMessageBox.confirm(
          '这将使用 AI 生成新的场景。是否继续？',
          '确认生成',
          {confirmButtonText: '生成', cancelButtonText: '取消', type: 'info'}
      );
    } catch {
      return; // 用户取消
    }
  }

  try {
    await chapterStore.generateChapterScenes(chapter_id);
    ElMessage.success('场景生成成功！');
    // 成功后，确保 chapterStore.chapters 被更新，或者手动触发一次 chapter 获取
    await chapterStore.fetchChapters(projectId.value); // 可选，如果 store action 没有更新本地 state
  } catch (err) {
    console.error('Scenes generation failed:', err);
    if (err) {
      ElMessage.error('场景生成失败！');
    }
    // 错误信息应由 store 处理并显示
  }
};

// 内容生成/优化 (基本不变)
const triggerContentGeneration = async () => {
  // ... (保持不变)
  if (!chapterStore.activeChapter) return;
  try {
    await ElMessageBox.confirm(
        '这将使用 AI 生成/优化章节内容，可能会覆盖现有内容。是否继续？',
        '确认操作',
        {confirmButtonText: '继续', cancelButtonText: '取消', type: 'warning'}
    );
  } catch {
    return; // 用户取消
  }
  isCreatingChapterContent.value = true; // 可以复用 loading 状态或创建新的
  try {
    await chapterStore.generateChapterContent(chapterStore.activeChapter.id);
    // 不需要手动设置 loading false，store action 应该处理
    ElMessage.success('小说内容操作成功！');
  } catch (err) {
    console.error('Content generation/optimization failed:', err);
    // 错误信息由 store 处理
  } finally {
    isCreatingChapterContent.value = false;
  }
};

// --- Lifecycle Hooks ---
onMounted(() => {
  fetchData();
});

watch(projectId, (newId, oldId) => {
  if (newId !== oldId && newId) {
    fetchData();
  }
});

watch(chapters, (newChapters) => {
  if (selectedChapterId.value && !newChapters.some(c => c.id === selectedChapterId.value)) {
    selectedChapterId.value = null;
  }
  // Handle chapterToDelete consistency if chapters change while confirm is pending
  if (chapterToDelete.value && !newChapters.some(c => c.id === chapterToDelete.value.id)) {
    chapterToDelete.value = null; // Chapter was deleted externally, cancel pending confirm
    if (chapterDeleteConfirmRef.value?.close) {
      chapterDeleteConfirmRef.value.close();
    }
  }
}, {deep: true}); // Deep watch might be needed if scenes inside chapters change

watch(volumes, (newVolumes) => {
  const existingVolumeIds = new Set(newVolumes.map(v => v.id.toString()));
  activeVolumeIds.value = activeVolumeIds.value.filter(id => existingVolumeIds.has(id));
});


</script>

<style scoped>
.structure-editor-view {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.volume-list {
  border-top: 1px solid var(--el-border-color-light);
  border-bottom: 1px solid var(--el-border-color-light);
}

.el-collapse-item :deep(.el-collapse-item__header) {
  border-bottom: 1px solid var(--el-border-color-lighter);
  padding: 0 15px;
  height: 48px;
  line-height: 48px;
}

.el-collapse-item:last-child :deep(.el-collapse-item__header) {
  border-bottom: none;
}

.el-collapse-item :deep(.el-collapse-item__content) {
  padding-bottom: 0; /* Remove default padding */
}


.volume-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.volume-title {
  font-weight: bold;
  font-size: 1.1em;
  flex-grow: 1;
  margin-right: 20px;
}

.volume-actions {
  flex-shrink: 0;
}

.volume-actions .el-button {
  margin-left: 8px;
}

.chapter-list-in-volume {
  padding: 10px 15px; /* Provide padding around the list of ChapterItems */
  background-color: #fdfdfd;
}


.empty-list {
  padding: 30px 0;
  text-align: center;
}

.empty-list.inside-volume {
  padding: 20px 0;
}

/* Keep dialog styles */
.dialog-footer {
  text-align: right;
}

.content-loading {
  padding: 20px;
}
</style>