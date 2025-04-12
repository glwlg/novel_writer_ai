<template>
  <div class="structure-editor-view" v-loading="isLoadingOverall||isGenerating"
       :element-loading-text="isGenerating?'生成中...':'加载中...'">
    <!-- 页面头部 -->
    <el-page-header @back="goBackToProject" :content="pageTitle" class="page-header">
      <template #extra>
        <!-- 新建卷按钮 -->
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
      <el-col :span="24">
        <!-- 卷列表为空时的提示 -->
        <div v-if="!sortedVolumesWithChapters || sortedVolumesWithChapters.length === 0 && !isLoadingOverall"
             class="empty-list">
          <el-empty description="还没有创建任何卷，点击右上角“新建卷”开始吧！"></el-empty>
        </div>
        <!-- 卷列表折叠面板 -->
        <el-collapse v-model="activeVolumeIds" v-else class="volume-list">
          <!-- 使用 VolumeItem 组件循环渲染卷 -->
          <VolumeItem
              v-for="volume in sortedVolumesWithChapters"
              :key="volume.id"
              :volume="volume"
              :selected-chapter-id="selectedChapterId"
              @edit="openEditVolumeDialog"
              @delete="confirmDeleteVolume"
              @create-chapter="openCreateChapterDialog"
              @select-chapter="selectChapter"
              @edit-chapter="openEditChapterDialog"
              @delete-chapter="confirmDeleteChapter"
              @generate-scenes="triggerScenesGeneration"
              @generate-scene-content="triggerGenerateSceneContent"
              @view-chapter="openChapterDialog"
          />
        </el-collapse>
      </el-col>
    </el-row>

    <!-- 对话框：创建/编辑卷 -->
    <el-dialog v-model="volumeDialogVisible" :title="isEditingVolume ? '编辑卷' : '新建卷'" width="500px"
               @closed="resetVolumeForm" :close-on-click-modal="false">
      <!-- 使用 VolumeForm 组件 -->
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

    <!-- 对话框：创建/编辑章节 -->
    <el-dialog v-model="chapterDialogVisible" :title="isEditingChapter ? '编辑章节' : '新建章节'" width="500px"
               @closed="resetChapterForm" :close-on-click-modal="false">
      <!-- 使用 ChapterForm 组件 -->
      <ChapterForm
          v-if="chapterDialogVisible"
          :project-id="projectId"
          :initial-data="chapterFormData"
          :is-editing="isEditingChapter"
          :is-loading="isSavingChapter"
          @save="saveChapter"
          @cancel="chapterDialogVisible = false"/>
    </el-dialog>

    <!-- 对话框：查看/编辑小说章节内容 -->
    <el-dialog v-model="chapterContentDialogVisible" :title="chapterStore.activeChapter?.title || '章节内容'"
               width="60vw"
               @closed="chapterStore.clearActiveChapter()" :close-on-click-modal="false">
      <!-- 内容加载状态 -->
      <div v-if="isCreatingChapterContent" class="content-loading">
        <el-skeleton :rows="5" animated/>
      </div>
      <!-- 富文本编辑器 -->
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
      <!-- 对话框底部操作 -->
      <template #footer>
         <span class="dialog-footer">
           <el-button @click="chapterContentDialogVisible = false">关闭</el-button>
           <el-button type="primary" @click="triggerContentGeneration" :loading="isCreatingChapterContent"
                      :icon="MagicStick">
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
// --- 状态管理 ---
import {useVolumeStore} from '@/store/volume';
import {useChapterStore} from '@/store/chapter';
import {useSceneStore} from '@/store/scene';
import {useProjectStore} from '@/store/project';
// --- UI 组件 ---
import {
  ElPageHeader,
  ElButton,
  ElAlert,
  ElRow,
  ElCol,
  ElCollapse,
  ElEmpty,
  ElDialog,
  ElSkeleton,
  ElMessage,
  ElMessageBox,
  ElPopconfirm
} from 'element-plus';
import {MagicStick, Plus} from '@element-plus/icons-vue';
// --- 自定义组件 ---
import VolumeItem from '@/components/volume/VolumeItem.vue'; // 引入卷条目组件
import VolumeForm from '@/components/volume/VolumeForm.vue'; // 引入卷表单组件
import ChapterForm from '@/components/chapter/ChapterForm.vue'; // 章节表单组件
import RichTextEditor from "@/components/common/RichTextEditor.vue"; // 富文本编辑器

// --- Router & Route ---
const route = useRoute();
const router = useRouter();
// 从路由参数获取项目ID
const projectId = computed(() => parseInt(route.params.projectId, 10));

// --- 状态管理实例 ---
const volumeStore = useVolumeStore();
const chapterStore = useChapterStore();
const sceneStore = useSceneStore();
const projectStore = useProjectStore();

// --- 组件内部状态 ---
// 当前选中的章节ID
const selectedChapterId = ref(null);
// 当前展开的卷ID列表 (用于 el-collapse)
const activeVolumeIds = ref([]);

// --- 卷相关状态 ---
// 创建/编辑卷对话框可见性
const volumeDialogVisible = ref(false);
// 是否是编辑卷模式
const isEditingVolume = ref(false);
// 卷表单数据
const volumeFormData = ref({id: null, title: '', summary: '', order: 0});
// 卷表单组件引用
const volumeFormComponentRef = ref(null);
// 是否正在保存卷
const isSavingVolume = ref(false);

// --- 章节相关状态 ---
// 创建/编辑章节对话框可见性
const chapterDialogVisible = ref(false);
// 是否是编辑章节模式
const isEditingChapter = ref(false);
// 章节表单数据
const chapterFormData = ref({id: null, volume_id: null, title: '', summary: '', order: 0, content: ''});
// 是否正在保存章节
const isSavingChapter = ref(false);

// --- 章节内容对话框状态 ---
// 章节内容对话框可见性
const chapterContentDialogVisible = ref(false);
// 是否正在生成章节内容
const isCreatingChapterContent = ref(false);


// --- 计算属性 ---
// 整体加载状态，取决于卷和章节是否正在加载
const isLoadingOverall = computed(() => volumeStore.isLoading || chapterStore.isLoading || sceneStore.isLoading);
const isGenerating = computed(() => volumeStore.isGenerating || chapterStore.isGenerating || sceneStore.isGenerating);
// 页面标题
const pageTitle = computed(() => projectStore.currentProject ? `${projectStore.currentProject.title} - 故事结构` : '故事结构');
// 统一的错误信息显示
const errorMsg = computed(() => volumeStore.error || chapterStore.error || sceneStore.error);

// --- 从 Store 获取数据 ---
// 卷列表
const volumes = computed(() => volumeStore.volumes);
// 章节列表
const chapters = computed(() => chapterStore.chapters);
// 场景列表
const scenes = computed(() => sceneStore.scenes);

// --- 数据处理与组合 ---
// 将章节按卷ID分组，并附加场景信息
const volumesWithChapters = computed(() => {
  // return volumes.value;
  const volumeMap = {};
  // 初始化卷Map，每个卷包含一个空的 chapters 数组
  volumes.value.forEach(vol => {
    volumeMap[vol.id] = {...vol, chapters: []};
  });

  const chapterMap = {};
  // 初始化章节Map，每个章节包含一个空的 scenes 数组
  chapters.value.forEach(chap => {
    chapterMap[chap.id] = {...chap, scenes: []};
    // 将章节放入对应卷的 chapters 数组中
    if (volumeMap[chap.volume_id]) {
      // 直接将 chapterMap 中的引用放入，后续场景会填充到这个引用里
      volumeMap[chap.volume_id].chapters.push(chapterMap[chap.id]);
    } else {
      console.warn(`章节 ${chap.id} 的 volume_id ${chap.volume_id} 无效或卷未找到`);
    }
  });

  // 将场景按 chapter_id 分配到 chapterMap 中对应章节的 scenes 数组
  scenes.value.forEach(scene => {
    if (chapterMap[scene.chapter_id]) {
      chapterMap[scene.chapter_id].scenes.push({...scene});
    } else {
      // 理论上不应发生，除非数据不一致
      console.warn(`场景 ${scene.id} 的 chapter_id ${scene.chapter_id} 无效或章节未找到`);
    }
  });

  // 返回处理后的卷列表
  return Object.values(volumeMap);
});

// 对包含章节的卷列表进行排序
const sortedVolumesWithChapters = computed(() => {
  return [...volumesWithChapters.value].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
});

// --- 方法 ---

// --- 数据获取与初始化 ---
// 获取项目相关数据（卷、章节、场景）
const fetchData = async () => {
  if (!projectId.value || isNaN(projectId.value)) {
    ElMessage.error('无效的项目 ID');
    router.push({name: 'ProjectDashboard'}); // 跳转回项目仪表盘
    return;
  }
  // 清除旧错误
  clearErrors();
  try {
    // 确保项目详情已加载
    await projectStore.fetchProjectDetails(projectId.value);

    await volumeStore.fetchVolumes(projectId.value);

    // 数据加载成功后，默认展开第一个卷（如果存在）
    if (sortedVolumesWithChapters.value.length > 0) {
      // 确保 ID 转为字符串，因为 el-collapse v-model 需要字符串数组
      activeVolumeIds.value = [sortedVolumesWithChapters.value[0].id.toString()];
    } else {
      activeVolumeIds.value = []; // 没有卷则不展开
    }
  } catch (error) {
    console.error("获取结构数据失败:", error);
    // 错误消息已通过 computed 属性 errorMsg 显示在 el-alert 中
  } finally {
    // 初始状态下不选中任何章节
    selectedChapterId.value = null;
  }
};

// 清除 Store 中的错误状态
const clearErrors = () => {
  volumeStore._setError(null);
  chapterStore._setError(null);
  sceneStore._setError(null);
};

// 返回项目仪表盘
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


// --- 章节 CRUD 操作 ---

// 选择章节（由 VolumeItem 转发的 @select-chapter 事件触发）
const selectChapter = (chapterId) => {
  // 如果点击的是已选中的章节，则取消选中；否则选中该章节
  selectedChapterId.value = selectedChapterId.value === chapterId ? null : chapterId;
};

// 打开新建章节对话框（由 VolumeItem 的 @create-chapter 事件触发）
const openCreateChapterDialog = (volumeId) => {
  if (!volumeId) {
    ElMessage.warning("无法确定所属卷，请重试");
    return;
  }
  isEditingChapter.value = false; // 设置为非编辑模式
  // 找到父卷以计算新章节的默认排序
  const parentVolume = volumesWithChapters.value.find(v => v.id === volumeId);
  const maxOrder = parentVolume ? parentVolume.chapters.reduce((max, ch) => Math.max(max, ch.order ?? -1), -1) : -1;
  // 设置章节表单初始数据，预填 volume_id
  chapterFormData.value = {id: null, volume_id: volumeId, title: '', summary: '', order: maxOrder + 1, content: ''};
  chapterDialogVisible.value = true; // 显示对话框
};

// 打开编辑章节对话框（由 VolumeItem 转发的 @edit-chapter 事件触发）
const openEditChapterDialog = (chapter) => {
  isEditingChapter.value = true; // 设置为编辑模式
  // 使用传入的章节数据填充表单 (浅拷贝)
  chapterFormData.value = {...chapter};
  chapterDialogVisible.value = true; // 显示对话框
};

// 关闭章节对话框时重置表单状态
const resetChapterForm = () => {
  isEditingChapter.value = false;
  // ChapterForm 组件应能处理内部状态重置
  // chapterFormData.value = {id: null, volume_id: null, title: '', summary: '', order: 0, content: ''};
};

// 保存章节（由 ChapterForm 的 @save 事件触发）
const saveChapter = async (saveData) => {
  if (!saveData || !saveData.data) return; // 检查传入数据有效性
  isSavingChapter.value = true; // 开始保存
  const dataToSave = {
    volume_id: saveData.data.volume_id, // 确保包含 volume_id
    title: saveData.data.title,
    summary: saveData.data.summary,
    order: saveData.data.order,
    // content: saveData.data.content // 根据 ChapterForm 是否传递 content 决定是否保存
  };
  try {
    if (isEditingChapter.value) {
      // 编辑模式
      await chapterStore.updateChapter(saveData.id, dataToSave);
      ElMessage.success('章节已更新');
    } else {
      // 新建模式
      await chapterStore.createChapter(projectId.value, saveData.data.volume_id, dataToSave);
      ElMessage.success('章节已创建');
    }
    chapterDialogVisible.value = false; // 关闭对话框
    // 可能需要刷新场景数据，如果章节信息影响场景
    // await sceneStore.fetchScenes(projectId.value);
  } catch (error) {
    console.error('保存章节失败:', error);
    ElMessage.error(`保存章节失败: ${error.message || '未知错误'}`);
  } finally {
    isSavingChapter.value = false; // 结束保存
  }
};

// 确认删除章节（由 VolumeItem 转发的 @delete-chapter 事件触发）
const confirmDeleteChapter = async (chapterId) => {
  if (!chapterId) return;
  const chapter = chapterStore.chapters.find(ch => ch.id === chapterId);
  if (!chapter) {
    ElMessage.error("找不到要删除的章节信息");
    return;
  }

  // 弹出确认框
  try {
    await ElMessageBox.confirm(
        `确定删除章节 "${chapter.title}" 吗？章节下的所有场景也会被删除！`,
        '确认删除',
        {
          confirmButtonText: '确认删除',
          cancelButtonText: '取消',
          type: 'warning',
        }
    );
    // 用户确认后执行删除
    await chapterStore.deleteChapter(chapterId);
    ElMessage.success(`章节 "${chapter.title}" 及内部场景已删除`);
    // 如果删除的是当前选中的章节，取消选中状态
    if (selectedChapterId.value === chapterId) {
      selectedChapterId.value = null;
    }
  } catch (error) {
    if (error === 'cancel') {
      // 用户点击取消，不做任何事
      return;
    }
    // 删除过程中发生错误
    console.error('删除章节失败:', error);
    ElMessage.error(`删除章节失败: ${error.message || '未知错误'}`);
  }
};

// --- 章节内容与场景生成 ---

// 打开章节内容对话框（由 VolumeItem 转发的 @view-chapter 事件触发）
const openChapterDialog = async (chapterId) => {
  if (!chapterId) return;
  // 尝试从 store 中查找章节
  const chapter = chapterStore.chapters.find(ch => ch.id === chapterId);
  if (chapter) {
    // 可选：如果内容不是总加载，这里可以触发一次详细加载
    // await chapterStore.fetchChapterDetails(chapterId);
    // 设置 store 中的活动章节
    chapterStore.setActiveChapter(chapterId);
    // 确保活动章节已设置成功
    if (chapterStore.activeChapter) {
      chapterContentDialogVisible.value = true; // 显示内容对话框
    } else {
      ElMessage.error("无法加载章节详细信息");
    }
  } else {
    ElMessage.error("找不到章节信息");
  }
};

// 触发章节内场景的 AI 生成（由 VolumeItem 转发的 @generate-scenes 事件触发）
const triggerScenesGeneration = async (chapterId) => {
  if (!chapterId) return;
  const chapter = chapterStore.chapters.find(ch => ch.id === chapterId);
  if (!chapter) {
    ElMessage.error("找不到对应的章节");
    return;
  }

  // 检查是否已有场景，并进行相应提示
  const existingScenesCount = chapter.scenes?.length || 0;
  const confirmAction = existingScenesCount > 0 ?
      ElMessageBox.confirm(
          '该章节已存在场景，重新生成将覆盖现有场景。是否继续？',
          '确认覆盖生成',
          {confirmButtonText: '确认生成', cancelButtonText: '取消', type: 'warning'}
      ) :
      ElMessageBox.confirm(
          '这将使用 AI 生成新的场景。是否继续？',
          '确认生成',
          {confirmButtonText: '生成', cancelButtonText: '取消', type: 'info'}
      );

  try {
    await confirmAction; // 等待用户确认
  } catch (cancel) {
    return; // 用户取消
  }

  // 用户确认后，执行生成操作
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

// 触发章节内场景的 AI 生成（由 VolumeItem 转发的 @generate-scenes 事件触发）
const triggerGenerateSceneContent = async (sceneId) => {
  if (!sceneId) return;
  const scene = sceneStore.scenes.find(sc => sc.id === sceneId);
  if (!scene) {
    ElMessage.error("找不到对应的场景");
    return;
  }
  try {
    await sceneStore.generateSceneContent(sceneId);
    ElMessage.success('场景内容生成成功！');
    await sceneStore.fetchScenes(projectId.value);

  } catch (err) {
    // 错误信息已在 store 中设置，并会显示在 Alert 中
    console.error('RAG generation failed:', err);
  }
};

// 触发章节内容生成/优化（在章节内容对话框中操作）
const triggerContentGeneration = async () => {
  if (!chapterStore.activeChapter) return;
  // 确认操作
  try {
    await ElMessageBox.confirm(
        '这将使用 AI 生成/优化章节内容，可能会覆盖现有内容。是否继续？',
        '确认操作',
        {confirmButtonText: '继续', cancelButtonText: '取消', type: 'warning'}
    );
  } catch (cancel) {
    return; // 用户取消
  }

  isCreatingChapterContent.value = true; // 设置加载状态
  try {
    // 调用 store action 生成内容
    await chapterStore.generateChapterContent(chapterStore.activeChapter.id);
    ElMessage.success('章节内容操作成功！');
    // 内容更新应通过 v-model 自动反映在编辑器中
  } catch (err) {
    console.error('章节内容生成/优化失败:', err);
    ElMessage.error(`内容生成/优化失败: ${err.message || '未知错误'}`);
  } finally {
    isCreatingChapterContent.value = false; // 清除加载状态
  }
};

// --- 生命周期钩子 ---
// 组件挂载后获取初始数据
onMounted(() => {
  fetchData();
});

// --- 监听器 ---
// 监听项目ID变化，重新获取数据
watch(projectId, (newId, oldId) => {
  if (newId !== oldId && newId && !isNaN(newId)) {
    fetchData();
  }
});

// 监听章节列表变化，处理选中章节被删除的情况
watch(chapters, (newChapters) => {
  // 如果当前选中的章节ID在新列表中不存在，则取消选中
  if (selectedChapterId.value && !newChapters.some(c => c.id === selectedChapterId.value)) {
    selectedChapterId.value = null;
  }
}, {deep: true}); // 使用 deep watch 以便章节内部属性（如场景列表）变化也能触发

// 监听卷列表变化，更新展开状态
watch(volumes, (newVolumes) => {
  const existingVolumeIds = new Set(newVolumes.map(v => v.id.toString()));
  // 过滤掉 activeVolumeIds 中不再存在的卷ID
  activeVolumeIds.value = activeVolumeIds.value.filter(id => existingVolumeIds.has(id));
});

</script>

<style scoped>
/* 页面整体内边距 */
.structure-editor-view {
  padding: 20px;
}

/* 页面头部样式 */
.page-header {
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--el-border-color-light);
}

/* 卷列表容器样式 */
.volume-list {
  border-top: 1px solid var(--el-border-color-light); /* 顶部边框 */
  /* 移除底部边框，由最后一个 CollapseItem 处理 */
}

/* Element Plus Collapse Item 头部通用样式 */
.el-collapse-item :deep(.el-collapse-item__header) {
  /* 覆盖默认样式或添加自定义样式 */
  border-bottom: 1px solid var(--el-border-color-lighter); /* 底部边框 */
  padding: 0 15px; /* 左右内边距 */
  height: 48px; /* 固定高度 */
  line-height: 48px; /* 垂直居中 */
}

/* 最后一个 Collapse Item 的头部移除底部边框 */
.el-collapse-item:last-child :deep(.el-collapse-item__header) {
  border-bottom: none;
}

/* 空列表提示样式 */
.empty-list {
  padding: 30px 0;
  text-align: center;
}

/* 对话框底部通用样式 */
.dialog-footer {
  text-align: right;
}

/* 内容加载时的骨架屏容器样式 */
.content-loading {
  padding: 20px;
}

</style>