<template>
  <div class="structure-editor-view" v-loading="isLoadingOverall||isGenerating"
       :element-loading-text="isGenerating?'生成中...':'加载中...'">
    <!-- 页面头部 -->
    <el-page-header @back="goBackToProject" :content="pageTitle" class="page-header">
      <template #extra>
        <el-button type="primary" @click="openCreateVolumeDialog" :icon="Plus">新建卷</el-button>
      </template>
    </el-page-header>

    <!-- 错误提示 -->
    <el-alert v-if="errorMsg"
              :title="`加载数据时出错: ${errorMsg}`" type="error"
              show-icon closable
              @close="clearErrors"/>

    <!-- 主要内容区域 -->
    <el-row :gutter="20">
      <!-- 左侧：卷、章节、场景结构树 -->
      <el-col :span="8">
        <div v-if="!sortedVolumesWithChapters || sortedVolumesWithChapters.length === 0 && !isLoadingOverall"
             class="empty-list">
          <el-empty description="还没有创建任何卷，点击右上角“新建卷”开始吧！"></el-empty>
        </div>
        <el-collapse v-model="activeVolumeIds" v-else class="volume-list">
          <!-- 使用 VolumeItem 组件循环渲染卷 -->
          <VolumeItem
              v-for="volume in sortedVolumesWithChapters"
              :key="volume.id"
              :volume="volume"
              :selected-chapter-id="selectedChapterId"
              :selected-scene-id="selectedSceneId"
              @edit="openEditVolumeDialog"
              @delete="confirmDeleteVolume"
              @create-chapter="openCreateChapterDialog"
              @select-chapter="selectChapter"
              @edit-chapter="openEditChapterDialog"
              @delete-chapter="confirmDeleteChapter"
              @generate-scenes="triggerScenesGeneration"
              @generate-scene-content="triggerGenerateSceneContent"
              @select-scene="selectScene"
          />
        </el-collapse>
      </el-col>

      <!-- 右侧：章节内容 或 场景详情 -->
      <el-col :span="16">
        <el-card shadow="never" class="detail-card" v-loading="isLoadingDetail">
          <template #header>
            <div class="content-card-header">
              <!-- 场景标题 (优先显示场景) -->
              <span v-if="selectedSceneId && activeSceneDetails">
                    {{ '场景' + (activeSceneDetails.order_in_chapter + 1) + ': ' + activeSceneDetails.title }}
                </span>
              <!-- 章节标题 (无选中场景时显示章节) -->
              <span v-else-if="selectedChapterId && activeChapterDetails">
                 第 {{ activeChapterDetails.order + 1 }} 章:  {{ activeChapterDetails.title }}
                </span>
              <!-- 未选择时的标题 -->
              <span v-else>详情</span>

              <!-- 章节操作按钮 (仅当选中章节且未选中场景时显示) -->
              <div v-if="selectedChapterId && !selectedSceneId && activeChapterDetails">
                <el-button type="primary" :icon="MagicStick" size="small" @click="triggerContentGeneration"
                           :loading="isGenerating || isCreatingChapterContent">
                  {{ activeChapterDetails.content ? '重新生成' : '根据场景内容生成' }}
                </el-button>
                <el-button type="primary" size="small" @click="saveChapterContent" :loading="isSavingChapter">保存内容
                </el-button>
              </div>
              <!-- 场景操作按钮将在 SceneDetailPanel 内部处理 -->
            </div>
          </template>

          <!-- 条件渲染：场景详情面板 (优先渲染) -->
          <SceneDetailPanel
              v-if="selectedSceneId"
              :key="selectedSceneId"
              :scene-id="selectedSceneId"
              @close="handleSceneDetailClose"
              @scene-deleted="handleSceneDeleted"
              @scene-save="handleSceneUpdated"
          />

          <!-- 条件渲染：章节内容编辑器 (无选中场景，但有选中章节时渲染) -->
          <div v-else-if="selectedChapterId && activeChapterDetails">
            <div v-if="isGenerating || isCreatingChapterContent" class="content-loading">
              <el-skeleton :rows="5" animated/>
            </div>
            <div v-else>
              <!-- 注意：v-model 现在直接绑定 activeChapterDetails 的 content -->
              <RichTextEditor
                  style="height: calc(100% - 10px);"
                  v-model="activeChapterDetails.content"
                  :editorProps="{
                    attributes: {
                      class: 'prose prose-sm sm:prose lg:prose-lg xl:prose-2xl m-5 focus:outline-none',
                    },
                  }"
              />
            </div>
          </div>

          <!-- 条件渲染：未选择任何内容时的提示 -->
          <el-empty v-else description="请在左侧选择一个章节或场景查看详情"></el-empty>

        </el-card>
      </el-col>
    </el-row>

    <!-- 对话框：创建/编辑卷 (保持不变) -->
    <el-dialog v-model="volumeDialogVisible" :title="isEditingVolume ? '编辑卷' : '新建卷'" width="500px"
               @closed="resetVolumeForm" :close-on-click-modal="false">
      <VolumeForm
          v-if="volumeDialogVisible"
          :initial-data="volumeFormData"
          :is-editing="isEditingVolume"
          :is-loading="isSavingVolume"
          @save="handleSaveVolume"
          @cancel="volumeDialogVisible = false"
          ref="volumeFormComponentRef"
      />
    </el-dialog>

    <!-- 对话框：创建/编辑章节 (保持不变) -->
    <el-dialog v-model="chapterDialogVisible" :title="isEditingChapter ? '编辑章节' : '新建章节'" width="500px"
               @closed="resetChapterForm" :close-on-click-modal="false">
      <ChapterForm
          v-if="chapterDialogVisible"
          :project-id="projectId"
          :initial-data="chapterFormData"
          :is-editing="isEditingChapter"
          :is-loading="isSavingChapter"
          @save="saveChapter"
          @cancel="chapterDialogVisible = false"/>
    </el-dialog>

  </div>
</template>

<script setup>
import {computed, nextTick, onMounted, ref, watch} from 'vue';
import {useRoute, useRouter} from 'vue-router';
// --- 状态管理 ---
import {useVolumeStore} from '@/store/volume';
import {useChapterStore} from '@/store/chapter';
import {useSceneStore} from '@/store/scene';
import {useProjectStore} from '@/store/project';
// --- UI 组件 ---
import {
  ElAlert,
  ElButton,
  ElCard,
  ElCol,
  ElCollapse,
  ElDialog,
  ElEmpty,
  ElMessage,
  ElMessageBox,
  ElPageHeader,
  ElRow,
  ElSkeleton
} from 'element-plus';
import {MagicStick, Plus} from '@element-plus/icons-vue';
// --- 自定义组件 ---
import VolumeItem from '@/components/volume/VolumeItem.vue';
import VolumeForm from '@/components/volume/VolumeForm.vue';
import ChapterForm from '@/components/chapter/ChapterForm.vue';
import RichTextEditor from "@/components/common/RichTextEditor.vue";
import SceneDetailPanel from '@/components/scene/SceneDetailPanel.vue'; // 引入新的场景详情面板组件

// --- Router & Route ---
const route = useRoute();
const router = useRouter();
const projectId = computed(() => parseInt(route.params.projectId, 10));

// --- 状态管理实例 ---
const volumeStore = useVolumeStore();
const chapterStore = useChapterStore();
const sceneStore = useSceneStore();
const projectStore = useProjectStore();

// --- 组件内部状态 ---
const selectedChapterId = ref(null); // 保留：当前选中的章节ID
const selectedSceneId = ref(null);   // 新增：当前选中的场景ID
const activeVolumeIds = ref([]);     // 当前展开的卷ID列表

// --- 卷相关状态 (保持不变) ---
const volumeDialogVisible = ref(false);
const isEditingVolume = ref(false);
const volumeFormData = ref({id: null, title: '', summary: '', order: 0});
const volumeFormComponentRef = ref(null);
const isSavingVolume = ref(false);

// --- 章节相关状态 (保持不变) ---
const chapterDialogVisible = ref(false);
const isEditingChapter = ref(false);
const chapterFormData = ref({id: null, volume_id: null, title: '', summary: '', order: 0, content: ''});
const isSavingChapter = ref(false);
const isCreatingChapterContent = ref(false);


// --- 计算属性 ---
const isLoadingOverall = computed(() => volumeStore.isLoading || chapterStore.isLoading || sceneStore.isLoading);
const isLoadingDetail = computed(() => chapterStore.isLoadingDetails || sceneStore.isLoadingDetails);
// 合并生成状态，包括章节内容生成
const isGenerating = computed(() =>
    volumeStore.isGenerating ||
    chapterStore.isGenerating ||
    sceneStore.isGenerating ||
    isCreatingChapterContent.value // 加入章节内容生成状态
);
const pageTitle = computed(() => projectStore.currentProject ? `${projectStore.currentProject.title} - 故事结构` : '故事结构');
const errorMsg = computed(() => volumeStore.error || chapterStore.error || sceneStore.error || sceneStore.generationError); // 合并错误

// --- 从 Store 获取数据 (保持不变) ---
const volumes = computed(() => volumeStore.volumes);
const chapters = computed(() => chapterStore.chapters);
const scenes = computed(() => sceneStore.scenes);

// --- 数据处理与组合 (保持不变) ---
const volumesWithChapters = computed(() => {
  // ... (此处省略，保持原有逻辑不变)
  const volumeMap = {};
  volumes.value.forEach(vol => {
    volumeMap[vol.id] = {...vol, chapters: []};
  });
  const chapterMap = {};
  chapters.value.forEach(chap => {
    // 重要: 在这里就确保每个 chapter 对象都包含 content，即使是空字符串
    chapterMap[chap.id] = {...chap, content: chap.content || '', scenes: []};
    if (volumeMap[chap.volume_id]) {
      volumeMap[chap.volume_id].chapters.push(chapterMap[chap.id]);
    } else {
      console.warn(`章节 ${chap.id} 的 volume_id ${chap.volume_id} 无效或卷未找到`);
    }
  });
  scenes.value.forEach(scene => {
    if (chapterMap[scene.chapter_id]) {
      chapterMap[scene.chapter_id].scenes.push({...scene});
    } else {
      console.warn(`场景 ${scene.id} 的 chapter_id ${scene.chapter_id} 无效或章节未找到`);
    }
  });
  // 排序
  Object.values(volumeMap).forEach(vol => {
    vol.chapters.sort((a, b) => (b.order ?? 0) - (a.order ?? 0));
    vol.chapters.forEach(chap => {
      chap.scenes.sort((a, b) => (b.order_in_chapter ?? 0) - (a.order_in_chapter ?? 0));
    });
  });
  return Object.values(volumeMap);
});
const sortedVolumesWithChapters = computed(() => {
  return [...volumesWithChapters.value].sort((a, b) => (b.order ?? 0) - (a.order ?? 0));
});

// --- 计算当前激活的章节和场景的详细信息 ---
// 用于在模板中方便地访问标题、内容等，并确保响应性
const activeChapterDetails = computed(() => {
  if (!selectedChapterId.value) return null;
  // 从处理后的数据结构中查找，确保 content 存在
  for (const volume of volumesWithChapters.value) {
    const chapter = volume.chapters.find(ch => ch.id === selectedChapterId.value);
    if (chapter) return chapter;
  }
  // 如果在 volumesWithChapters 没找到（理论上不应发生），尝试从原始 store 查找
  const found = chapterStore.chapters.find(ch => ch.id === selectedChapterId.value);
  // 确保返回的对象有 content 属性
  return found ? {...found, content: found.content || ''} : null;
});

const activeSceneDetails = computed(() => {
  if (!selectedSceneId.value) return null;
  // SceneDetailPanel 会自行加载，但我们可能需要在头部显示标题，所以从 sceneStore 查找
  return sceneStore.scenes.find(sc => sc.id === selectedSceneId.value) || sceneStore.activeScene; // 优先用列表，备用activeScene
});


// --- 方法 ---

// --- 数据获取与初始化 ---
const fetchData = async () => {
  if (!projectId.value || isNaN(projectId.value)) {
    ElMessage.error('无效的项目 ID');
    router.push({name: 'ProjectDashboard'});
    return;
  }
  clearErrors();
  try {
    await projectStore.fetchProjectDetails(projectId.value);
    await volumeStore.fetchVolumes(projectId.value);

    if (sortedVolumesWithChapters.value.length > 0) {
      activeVolumeIds.value = [sortedVolumesWithChapters.value[0].id.toString()];
      // 默认选中第一个卷的第一个章节（如果存在）
      const firstVolume = sortedVolumesWithChapters.value[0];
      if (firstVolume.chapters && firstVolume.chapters.length > 0) {
        selectChapter(firstVolume.chapters[0].id);
      } else {
        selectedChapterId.value = null;
        selectedSceneId.value = null;
      }
    } else {
      activeVolumeIds.value = [];
      selectedChapterId.value = null;
      selectedSceneId.value = null;
    }
    // 初始化不选中任何场景
    selectedSceneId.value = null;

  } catch (error) {
    console.error("获取结构数据失败:", error);
  }
};

// --- 错误处理和导航 (保持不变) ---
const clearErrors = () => {
  volumeStore._setError(null);
  chapterStore._setError(null);
  sceneStore._setError('list', null); // 区分列表错误
  sceneStore._setError('details', null); // 详情错误
  sceneStore._setError('generating', null); // 生成错误
};
const goBackToProject = () => {
  router.push({name: 'ProjectDashboard'});
};

// --- 卷 CRUD 操作 ---

// 打开新建卷对话框
const openCreateVolumeDialog = () => {
  isEditingVolume.value = false; // 设置为非编辑模式
  // 计算新卷的默认排序值（现有最大order + 1）
  const maxOrder = volumes.value.reduce((max, vol) => Math.max(max, vol.order ?? -1), -1);
  // 设置表单初始数据
  volumeFormData.value = {id: null, title: '', summary: '', order: maxOrder + 1, project_id: projectId.value};
  volumeDialogVisible.value = true; // 显示对话框
  // 对话框内容渲染后清除表单验证状态 (如果 VolumeForm 内部没有处理)
  nextTick(() => {
    volumeFormComponentRef.value?.resetForm(); // 调用 VolumeForm 的重置方法
  });
};

// 打开编辑卷对话框
const openEditVolumeDialog = (volume) => {
  isEditingVolume.value = true; // 设置为编辑模式
  volumeFormData.value = {...volume}; // 使用传入的卷数据填充表单 (浅拷贝)
  volumeDialogVisible.value = true; // 显示对话框
  // 对话框内容渲染后清除表单验证状态 (如果 VolumeForm 内部没有处理)
  nextTick(() => {
    // VolumeForm 内部的 watch 会自动更新并清空校验，这里可能不需要手动调用 reset
    // volumeFormComponentRef.value?.resetForm();
  });
};

// 关闭卷对话框时重置表单状态（主要重置编辑/新建状态标志）
const resetVolumeForm = () => {
  isEditingVolume.value = false;
  // VolumeForm 组件内部会处理字段重置
  // volumeFormData.value = {id: null, title: '', summary: '', order: 0};
};

// 处理保存卷事件（由 VolumeForm 的 @save 事件触发）
const handleSaveVolume = async (formDataFromForm) => {
  isSavingVolume.value = true; // 开始保存，设置加载状态
  const dataToSave = {
    title: formDataFromForm.title,
    summary: formDataFromForm.summary,
    order: formDataFromForm.order,
    project_id: projectId.value // 确保项目ID正确传递
  };
  try {
    if (isEditingVolume.value) {
      // 编辑模式，调用更新接口
      await volumeStore.updateVolume(formDataFromForm.id, dataToSave);
      ElMessage.success('卷已更新');
    } else {
      // 新建模式，调用创建接口
      await volumeStore.createVolume(projectId.value, dataToSave);
      ElMessage.success('卷已创建');
    }
    volumeDialogVisible.value = false; // 关闭对话框
  } catch (error) {
    console.error('保存卷失败:', error);
    // 错误应由 store 处理并在需要时显示，这里仅记录日志
    ElMessage.error(`保存卷失败: ${error.message || '未知错误'}`);
  } finally {
    isSavingVolume.value = false; // 结束保存，清除加载状态
  }
};

// 确认删除卷（由 VolumeItem 的 @delete 事件触发）
const confirmDeleteVolume = async (volume) => {
  try {
    // 调用 Store 中的删除方法
    await volumeStore.deleteVolume(volume.id);
    ElMessage.success(`卷 "${volume.title}" 及内容已删除`);
    // 如果被删除的卷当前是展开的，从 activeVolumeIds 中移除
    activeVolumeIds.value = activeVolumeIds.value.filter(id => id !== volume.id.toString());
  } catch (error) {
    console.error('删除卷失败:', error);
    ElMessage.error(`删除卷失败: ${error.message || '未知错误'}`);
    // 错误信息已在 store 中处理
  }
};


// 选择章节
const selectChapter = async (chapterId) => {
  // 如果点击的是当前已选中章节，且没有选中场景，则取消选择章节
  if (selectedChapterId.value === chapterId && !selectedSceneId.value) {
    selectedChapterId.value = null;
  } else {
    // 选择新章节或从场景返回章节
    selectedChapterId.value = chapterId;
    selectedSceneId.value = null; // 确保清除选中的场景
    if (!activeChapterDetails.value.content) {
      await chapterStore.fetchChapterDetail(chapterId); // 确保章节数据已加载
    }
  }
};

// 打开新建章节对话框 (保持不变)
const openCreateChapterDialog = (volumeId) => {
  if (!volumeId) {
    ElMessage.warning("无法确定所属卷，请重试");
    return;
  }
  isEditingChapter.value = false;
  const parentVolume = volumesWithChapters.value.find(v => v.id === volumeId);
  const maxOrder = parentVolume ? parentVolume.chapters.reduce((max, ch) => Math.max(max, ch.order ?? -1), -1) : -1;
  chapterFormData.value = {id: null, volume_id: volumeId, title: '', summary: '', order: maxOrder + 1, content: ''};
  chapterDialogVisible.value = true;
};
// 打开编辑章节对话框 (保持不变)
const openEditChapterDialog = (chapter) => {
  isEditingChapter.value = true;
  chapterFormData.value = {...chapter};
  chapterDialogVisible.value = true;
};
// 关闭章节对话框时重置表单 (保持不变)
const resetChapterForm = () => {
  isEditingChapter.value = false;
};
// 保存章节 (注意：创建后需要重新获取数据以获得content字段)
const saveChapter = async (saveData) => {
  if (!saveData || !saveData.data) return;
  isSavingChapter.value = true;
  const dataToSave = {
    volume_id: saveData.data.volume_id,
    title: saveData.data.title,
    summary: saveData.data.summary,
    order: saveData.data.order,
    // content 不在此处保存，通过编辑器单独保存
  };
  try {
    let savedChapterId;
    if (isEditingChapter.value) {
      await chapterStore.updateChapter(saveData.id, dataToSave);
      savedChapterId = saveData.id;
      ElMessage.success('章节已更新');
    } else {
      const newChapter = await chapterStore.createChapter(projectId.value, saveData.data.volume_id, dataToSave);
      savedChapterId = newChapter.id;
      ElMessage.success('章节已创建');
    }
    chapterDialogVisible.value = false;
    // 创建或更新后，重新获取章节数据以确保列表和 content 同步
    await chapterStore.fetchChapters(projectId.value);
    // 如果是新建，可以考虑选中这个新章节
    if (!isEditingChapter.value && savedChapterId) {
      // selectChapter(savedChapterId);
    }
  } catch (error) {
    console.error('保存章节失败:', error);
    ElMessage.error(`保存章节失败: ${error.message || '未知错误'}`);
  } finally {
    isSavingChapter.value = false;
  }
};
// 保存章节内容 - 使用 activeChapterDetails 计算属性
const saveChapterContent = async () => {
  if (!activeChapterDetails.value) {
    ElMessage.warning('没有选中的章节来保存内容');
    return;
  }
  isSavingChapter.value = true; // 可以复用这个加载状态
  const dataToSave = {
    content: activeChapterDetails.value.content, // 从计算属性获取当前编辑器的内容
  };
  try {
    await chapterStore.updateChapter(selectedChapterId.value, dataToSave);
    ElMessage.success('章节内容已保存');
  } catch (error) {
    console.error('保存章节内容失败:', error);
    ElMessage.error(`保存章节内容失败: ${error.message || '未知错误'}`);
  } finally {
    isSavingChapter.value = false;
  }
};

// 确认删除章节
const confirmDeleteChapter = async (chapterId) => {
  if (!chapterId) return;
  const chapter = chapterStore.chapters.find(ch => ch.id === chapterId);
  if (!chapter) {
    ElMessage.error("找不到要删除的章节信息");
    return;
  }
  try {
    await ElMessageBox.confirm(
        `确定删除章节 "${chapter.title}" 吗？章节下的所有场景也会被删除！`,
        '确认删除', { /* ... */}
    );
    await chapterStore.deleteChapter(chapterId);
    ElMessage.success(`章节 "${chapter.title}" 及内部场景已删除`);
    // 如果删除的是当前选中的章节，取消选中
    if (selectedChapterId.value === chapterId) {
      selectedChapterId.value = null;
      selectedSceneId.value = null; // 同时清除场景选择
    }
    // 刷新场景列表
    await sceneStore.fetchScenes(projectId.value);
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除章节失败:', error);
      ElMessage.error(`删除章节失败: ${error.message || '未知错误'}`);
    }
  }
};

// --- 场景相关操作 ---
// 选择场景
const selectScene = (sceneId) => {
  const scene = sceneStore.scenes.find(s => s.id === sceneId);
  if (!scene) {
    console.warn(`选择场景失败：未找到 ID 为 ${sceneId} 的场景`);
    return;
  }
  // 如果点击的是当前已选中场景，不做任何事（或可以选择取消选中，返回章节？）
  // if (selectedSceneId.value === sceneId) return;

  // 选择新场景
  selectedSceneId.value = sceneId;
  selectedChapterId.value = scene.chapter_id; // 自动选中其父章节
  // SceneDetailPanel 会根据 sceneId prop 加载数据
};

// 处理场景详情面板关闭事件
const handleSceneDetailClose = () => {
  // 关闭场景面板时，仅清除场景选择，章节选择状态保持不变
  selectedSceneId.value = null;
  // 此时右侧面板会自动显示 selectedChapterId 对应的章节内容
};

// 处理场景被删除事件 (由 SceneDetailPanel 发出)
const handleSceneDeleted = async (deletedSceneId) => {
  // 场景已在 Panel 内部处理删除，并触发了 close
  // 这里只需要确保数据是最新的
  // selectedSceneId 应该已经在 handleSceneDetailClose 中被设为 null
  // 刷新章节和场景数据以更新左侧列表
  await chapterStore.fetchChapters(projectId.value);
  await sceneStore.fetchScenes(projectId.value);
};

// 处理场景更新事件 (由 SceneDetailPanel 发出)
const handleSceneUpdated = async (updatedSceneId) => {
  // 场景数据已在 Panel 内部更新，这里刷新列表数据确保一致性
  console.log('handleSceneUpdated');
  // await sceneStore.fetchScenes(projectId.value);
  // 如果更新了标题等信息，章节数据也可能需要刷新（如果章节缓存了场景信息）
  // await chapterStore.fetchChapters(projectId.value);
  // 保持当前选中状态 (selectedSceneId 和 selectedChapterId) 不变
};


// --- 章节内容与场景生成 ---
// 触发章节内场景的 AI 生成（由 VolumeItem 转发）
const triggerScenesGeneration = async (chapterId) => {
  if (!chapterId) return;
  const chapter = chapterStore.chapters.find(ch => ch.id === chapterId);
  if (!chapter) { /* ... */
  }
  // ... (确认逻辑)
  try {
    const new_chapter_data = await chapterStore.generateChapterScenes(chapterId);
    ElMessage.success('场景生成任务已启动！');
    // 询问是否继续生成场景内容
    ElMessageBox.confirm(
        `场景列表生成成功！是否立即为这些新场景生成内容？`,
        '生成场景内容',
        {confirmButtonText: '立即生成', cancelButtonText: '稍后手动', type: 'success'}
    ).then(async () => {
      // 用户同意生成内容
      const scenesToGenerate = new_chapter_data?.scenes;
      if (!scenesToGenerate || scenesToGenerate.length === 0) {
        ElMessage.warning('未找到新生成的场景，无法生成内容。');
        // 即使没有场景，也最好刷新下章节数据
        await chapterStore.fetchChapters(projectId.value);
        await sceneStore.fetchScenes(projectId.value);
        return;
      }
      ElMessage.info(`开始为 ${scenesToGenerate.length} 个场景生成内容...`);
      // 异步并行（或串行，取决于后端能力和需求）生成场景内容
      const generationPromises = scenesToGenerate.map(scene => sceneStore.generateSceneContent(scene.id));
      await Promise.allSettled(generationPromises); // 等待所有生成完成（无论成功或失败）
      ElMessage.success('所有场景内容生成任务已完成！');
      // 生成后刷新数据
      await chapterStore.fetchChapters(projectId.value);
      await sceneStore.fetchScenes(projectId.value);

    }).catch(async () => {
      // 用户选择稍后手动生成，仅刷新数据
      ElMessage.info('您可以稍后在章节中手动为场景生成内容。');
      await chapterStore.fetchChapters(projectId.value);
      await sceneStore.fetchScenes(projectId.value);
    });

  } catch (err) {
    console.error('场景生成失败:', err);
    ElMessage.error(`场景生成失败: ${err.message || '未知错误'}`);
    // 可能需要刷新数据以显示部分成功的结果（如果可能）
    await chapterStore.fetchChapters(projectId.value);
    await sceneStore.fetchScenes(projectId.value);
  }
};
// 触发单个场景内容生成（由 VolumeItem 转发）
const triggerGenerateSceneContent = async (sceneId) => {
  if (!sceneId) return;
  const scene = sceneStore.scenes.find(sc => sc.id === sceneId);
  if (!scene) { /* ... */
  }
  try {
    await sceneStore.generateSceneContent(sceneId);
    ElMessage.success('场景内容生成成功！');
    // 刷新场景数据
    await sceneStore.fetchScenes(projectId.value);
    // 如果在 SceneDetailPanel 打开时触发，Panel 内部会处理更新
    // 如果在 VolumeItem 直接触发，确保列表更新
  } catch (err) { /* ... */
  }
};
// 触发章节内容生成/优化
const triggerContentGeneration = async () => {
  if (!selectedChapterId.value || !activeChapterDetails.value) {
    ElMessage.warning('请先选择一个章节');
    return;
  }
  // ... (确认逻辑)
  isCreatingChapterContent.value = true;
  try {
    // 注意：后端生成后应该返回更新后的内容
    const updatedChapter = await chapterStore.generateChapterContent(selectedChapterId.value);

    ElMessage.success('章节内容操作成功！');
  } catch (err) {
    console.error('章节内容生成/优化失败:', err);
    ElMessage.error(`内容生成/优化失败: ${err.message || '未知错误'}`);
  } finally {
    isCreatingChapterContent.value = false;
  }
};


// --- 生命周期钩子 ---
onMounted(() => {
  fetchData();
});

// --- 监听器 ---
watch(projectId, (newId, oldId) => {
  if (newId !== oldId && newId && !isNaN(newId)) {
    // 重置选择状态并重新加载数据
    selectedChapterId.value = null;
    selectedSceneId.value = null;
    fetchData();
  }
});

// 监听章节列表变化，处理选中章节被删除的情况
watch(chapters, (newChapters, oldChapters) => {
  if (selectedChapterId.value && !newChapters.some(c => c.id === selectedChapterId.value)) {
    // 如果当前选中的章节在新列表中不存在了
    selectedChapterId.value = null;
    selectedSceneId.value = null; // 相关的场景选择也应清除
  }
  // 深层比较新旧 chapters，检查 content 是否变化，如果是由外部（如生成）改变的，
  // 并且当前正在编辑该章节，可能需要提示用户或采取策略
  // (简单起见，暂时不处理外部内容冲突)

}, {deep: true});

// 监听场景列表变化，处理选中场景被删除的情况
watch(scenes, (newScenes) => {
  if (selectedSceneId.value && !newScenes.some(s => s.id === selectedSceneId.value)) {
    // 如果当前选中的场景在新列表中不存在了
    selectedSceneId.value = null;
    // 保持 selectedChapterId 不变，视图会自动回退到章节视图
  }
}, {deep: true});

// 监听卷列表变化 (保持不变)
watch(volumes, (newVolumes) => {
  const existingVolumeIds = new Set(newVolumes.map(v => v.id.toString()));
  activeVolumeIds.value = activeVolumeIds.value.filter(id => existingVolumeIds.has(id));
});

</script>

<style scoped>
/* ... (样式基本保持不变，可能需要微调 .detail-card 内富文本编辑器的高度计算) ... */
.structure-editor-view {
  padding: 20px;
  height: calc(100vh - 60px); /* 假设顶部导航栏高度为 60px */
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--el-border-color-light);
  flex-shrink: 0;
}

.el-row {
  flex-grow: 1;
  overflow: hidden;
}

.el-col {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.el-col:first-child {
  overflow-y: auto;
  border-right: 1px solid var(--el-border-color-light);
  padding-right: 10px !important;
}

.el-col:last-child {
  padding-left: 10px !important;
}

.detail-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.detail-card > :deep(.el-card__header) {
  flex-shrink: 0;
}

.detail-card > :deep(.el-card__body) {
  flex-grow: 1;
  overflow: hidden; /* 由内部组件管理滚动 */
  padding: 0;
  display: flex;
  flex-direction: column;
}

/* 确保 SceneDetailPanel 和 章节编辑器 div 能填满 */
.detail-card > :deep(.el-card__body) > .scene-detail-panel,
.detail-card > :deep(.el-card__body) > div:not(.el-empty) { /* 应用于章节编辑器包装器 */
  flex-grow: 1;
  overflow-y: auto;
  padding: 15px; /* 恢复内边距 */
  height: 100%; /* 尝试让内部元素感知高度 */
}

/* 章节编辑器内部的 RichTextEditor 高度 */
.detail-card > :deep(.el-card__body) > div > .RichTextEditor {
  height: 100%; /* 让编辑器填满其父 div */
}

/* 单独处理空状态的内边距 */
.detail-card :deep(.el-card__body) > .el-empty {
  padding: 20px;
  flex-grow: 1; /* 让空状态也占据空间 */
}

/* 移除 prose 的外边距，因为它在带 padding 的容器内 */
.detail-card :deep(.prose) {
  margin: 0 !important;
}

.volume-list {
  border-top: none;
}

.el-collapse-item :deep(.el-collapse-item__header) {
  border-bottom: 1px solid var(--el-border-color-lighter);
  padding: 0 10px;
  height: 40px;
  line-height: 40px;
}

.el-collapse-item:last-child :deep(.el-collapse-item__header) {
  border-bottom: none;
}

.empty-list {
  padding: 30px 0;
  text-align: center;
}

.dialog-footer {
  text-align: right;
}

.content-loading {
  padding: 20px;
}

.content-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 32px;
}

.content-card-header span {
  font-weight: bold;
  font-size: 1.1em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-right: 10px;
}
</style>