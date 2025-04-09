<template>
  <div class="structure-editor-view" v-loading="isLoadingOverall" element-loading-text="加载项目结构...">
    <el-page-header @back="goBackToProject" :content="pageTitle" class="page-header">
      <template #extra>
        <el-button type="primary" @click="openCreateChapterDialog" :icon="Plus">新建章节</el-button>
        <el-button type="success" @click="openCreateSceneDialog(null)" :icon="DocumentAdd">新建未分配场景</el-button>
      </template>
    </el-page-header>

    <el-alert v-if="chapterStore.error || sceneStore.error"
              :title="`加载结构数据时出错: ${chapterStore.error || sceneStore.error}`" type="error" show-icon closable
              @close="clearErrors"/>

    <el-row :gutter="20">
      <!-- 左侧：章节列表 -->
      <el-col :span="10">
        <el-card class="box-card chapters-card">
          <template #header>
            <div class="card-header">
              <span>章节列表</span>
              <el-tooltip content="拖拽章节进行排序" placement="top">
                <el-icon>
                  <Rank/>
                </el-icon>
              </el-tooltip>
            </div>
          </template>

          <div v-if="chapters.length === 0 && !chapterStore.isLoading" class="empty-list">
            <el-empty description="还没有章节，点击右上角“新建章节”开始创建吧！"></el-empty>
          </div>

          <!-- 使用 vue-draggable-next 进行章节拖拽排序 -->
          <draggable
              v-model="draggableChapters"
              tag="div"
              item-key="id"
              handle=".drag-handle-chapter"
              ghost-class="ghost-chapter"
              @end="onChapterDragEnd"
              v-else
              class="chapter-list"
          >
            <template #item="{ element: chapter }">
              <el-card shadow="never" class="chapter-item" :class="{ 'is-active': selectedChapterId === chapter.id }">
                <div class="chapter-header" @click="selectChapter(chapter.id)">
                  <span class="drag-handle-chapter">☰</span>
                  <span class="chapter-title">{{ chapter.title || '未命名章节' }} ({{
                      chapter.scenes?.length || 0
                    }} 场景)</span>
                  <div class="chapter-actions">
                    <el-button link type="primary" :icon="Edit" @click.stop="openEditChapterDialog(chapter)"
                               size="small"></el-button>
                    <el-button link type="danger" :icon="Delete" @click.stop="confirmDeleteChapter(chapter)"
                               size="small"></el-button>
                    <el-button link type="success" :icon="DocumentAdd" @click.stop="openCreateSceneDialog(chapter.id)"
                               size="small" title="在本章新建场景"></el-button>
                  </div>
                </div>
                <el-collapse-transition>
                  <div v-show="selectedChapterId === chapter.id" class="chapter-scenes">
                    <draggable
                        v-model="chapter.scenes"
                        tag="div"
                        item-key="id"
                        group="scenes"
                        :data-chapter-id="chapter.id"
                        handle=".scene-item"
                        ghost-class="ghost-scene"
                        drag-class="dragging-scene"
                        @end="onSceneDragEnd"
                        class="scene-list-in-chapter"
                    >
                      <template #item="{ element: scene }">
                        <SceneItem :scene="scene" class="draggable-scene-in-chapter"/>
                      </template>
                      <template #footer>
                        <div v-if="!chapter.scenes || chapter.scenes.length === 0" class="empty-scene-list">
                          <el-text size="small" type="info">暂无场景，可从“未分配”拖入或点击上方 '+' 新建</el-text>
                        </div>
                      </template>
                    </draggable>
                  </div>
                </el-collapse-transition>
              </el-card>
            </template>
          </draggable>

        </el-card>
      </el-col>

      <!-- 右侧：未分配场景列表 -->
      <el-col :span="14">
        <el-card class="box-card unassigned-scenes-card">
          <template #header>
            <div class="card-header">
              <span>未分配的场景</span>
              <el-tooltip content="可以将场景拖拽到左侧章节中" placement="top">
                <el-icon>
                  <Place/>
                </el-icon>
              </el-tooltip>
            </div>
          </template>

          <div v-if="unassignedScenes.length === 0 && !sceneStore.isLoadingUnassigned" class="empty-list">
            <el-empty description="没有未分配的场景"></el-empty>
          </div>

          <draggable
              v-model="draggableUnassignedScenes"
              tag="div"
              item-key="id"
              group="scenes"
              data-chapter-id="null"
              handle=".scene-item"
              ghost-class="ghost-scene"
              drag-class="dragging-scene"
              @end="onSceneDragEnd"
              v-else
              class="unassigned-scene-list"
          >
            <template #item="{ element: scene }">
              <SceneItem :scene="scene" class="draggable-scene-unassigned"/>
            </template>
          </draggable>
        </el-card>
      </el-col>
    </el-row>

    <!-- 对话框：创建/编辑章节 -->
    <el-dialog v-model="chapterDialogVisible" :title="isEditingChapter ? '编辑章节' : '新建章节'" width="500px"
               @closed="resetChapterForm">
      <el-form ref="chapterFormRef" :model="chapterFormData" :rules="chapterFormRules" label-position="top">
        <el-form-item label="章节标题" prop="title">
          <el-input v-model="chapterFormData.title" placeholder="请输入章节标题"/>
        </el-form-item>
        <el-form-item label="章节概要" prop="summary">
          <el-input v-model="chapterFormData.summary" type="textarea" :rows="3" placeholder="（可选）输入章节概要"/>
        </el-form-item>
        <el-form-item label="排序权重" prop="order">
          <el-input-number v-model="chapterFormData.order" :min="0" controls-position="right"/>
          <el-text size="small" type="info" style="margin-left: 10px;">数字越小越靠前</el-text>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="chapterDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveChapter" :loading="isSavingChapter">
            {{ isEditingChapter ? '保存修改' : '创建章节' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 对话框：创建场景 -->
    <el-dialog v-model="sceneDialogVisible" title="新建场景" width="600px" @closed="resetSceneForm">
      <el-form ref="sceneFormRef" :model="sceneFormData" :rules="sceneFormRules" label-position="top">
        <el-form-item label="场景目标/核心内容" prop="goal">
          <el-input
              v-model="sceneFormData.goal"
              type="textarea"
              :rows="3"
              placeholder="必须填写！简要描述这个场景需要达成的目标或核心情节"
              required
          />
        </el-form-item>
        <el-form-item label="场景标题" prop="title">
          <el-input v-model="sceneFormData.title" placeholder="（可选）给场景起个名字"/>
        </el-form-item>
        <el-form-item label="所属章节" prop="chapter_id">
          <el-select
              v-model="sceneFormData.chapter_id"
              placeholder="（可选）选择章节，留空则为未分配场景"
              clearable
              filterable
              style="width: 100%;"
          >
            <el-option
                v-for="chapter in chapters"
                :key="chapter.id"
                :label="chapter.title"
                :value="chapter.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="章节内排序" prop="order_in_chapter">
          <el-input-number v-model="sceneFormData.order_in_chapter" :min="0" controls-position="right"/>
          <el-text size="small" type="info" style="margin-left: 10px;">数字越小越靠前</el-text>
        </el-form-item>
      </el-form>
      <template #footer>
         <span class="dialog-footer">
           <el-button @click="sceneDialogVisible = false">取消</el-button>
           <el-button type="primary" @click="createScene" :loading="isCreatingScene">
             创建场景
           </el-button>
         </span>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import {ref, computed, onMounted, watch} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import {useChapterStore} from '@/store/chapter';
import {useSceneStore} from '@/store/scene';
import {useProjectStore} from '@/store/project';
import SceneItem from '@/components/scene/SceneItem.vue';
import draggable from 'vuedraggable'; // 导入 draggable
import {ElMessage, ElMessageBox} from 'element-plus';
import {Plus, Edit, Delete, Rank, Place, DocumentAdd} from '@element-plus/icons-vue';
import {nextTick} from 'vue';

// --- Router & Route ---
const route = useRoute();
const router = useRouter();
const projectId = computed(() => parseInt(route.params.projectId, 10));

// --- Stores ---
const chapterStore = useChapterStore();
const sceneStore = useSceneStore();
const projectStore = useProjectStore();

// --- State ---
const selectedChapterId = ref(null); // 当前展开/选中的章节ID
const chapterDialogVisible = ref(false);
const isEditingChapter = ref(false);
const chapterFormData = ref({id: null, title: '', summary: '', order: 0});
const chapterFormRef = ref(null);
const isSavingChapter = ref(false);

const sceneDialogVisible = ref(false);
const sceneFormData = ref({title: '', goal: '', chapter_id: null, order_in_chapter: 0});
const sceneFormRef = ref(null);
const isCreatingScene = ref(false);

// --- Computed ---
const isLoadingOverall = computed(() => chapterStore.isLoading || sceneStore.isLoadingUnassigned);
const pageTitle = computed(() => {
  if (projectStore.currentProject) {
    return `${projectStore.currentProject.title} - 故事结构`;
  }
  return '故事结构';
});
// 从 store 获取数据
const chapters = computed(() => chapterStore.chapters);

const chaptersMap = computed(() => {
  if (!Array.isArray(chapters.value)) {
    return {}; // 返回空 Map
  }
  return chapters.value.reduce((map, chapter) => {
    if (chapter && chapter.id !== undefined) {
      map[chapter.id] = chapter;
    }
    return map; // 返回累积的 map 给下一次迭代
  }, {}); // 初始值是一个空 Map
});
const unassignedScenes = computed(() => sceneStore.unassignedScenes);

// Draggable 需要直接操作数组，创建 ref 副本或直接用 store state (如果 store action 能处理好)
// 这里用 computed setter/getter 尝试同步 store (需要测试是否稳定)
const draggableChapters = computed({
  get: () => chapters.value,
  set: (newChapters) => {
    // 当拖拽库修改数组时，这里会被调用
    // 理论上 onChapterDragEnd 会处理更新逻辑
    // chapterStore.chapters = newChapters; // 不建议直接修改 store state
    console.log("Draggable updated chapters array internally.");
  }
});

const draggableUnassignedScenes = computed({
  get: () => unassignedScenes.value,
  set: (newScenes) => {
    // sceneStore.unassignedScenes = newScenes; // 不建议
    console.log("Draggable updated unassigned scenes array internally.");
  }
});


// 表单规则
const chapterFormRules = ref({
  title: [{required: true, message: '章节标题不能为空', trigger: 'blur'}],
});
const sceneFormRules = ref({
  goal: [{required: true, message: '场景目标不能为空', trigger: 'blur'}],
});

// --- Methods ---
const fetchData = async () => {
  if (!projectId.value) {
    ElMessage.error('无效的项目 ID');
    router.push({name: 'ProjectDashboard'});
    return;
  }
  // 确保项目详情已加载（包含项目名称等）
  if (!projectStore.currentProject || projectStore.currentProject.id !== projectId.value) {
    await projectStore.fetchProjectDetails(projectId.value);
    // fetchProjectDetails 内部应该已经调用了 fetchChapters 和 fetchUnassignedScenes
  } else {
    // 如果项目已加载，可能需要手动刷新章节和场景列表
    await Promise.all([
      chapterStore.fetchChapters(projectId.value),
      sceneStore.fetchUnassignedScenes(projectId.value)
    ]);
  }
  // 初始时不选中任何章节
  selectedChapterId.value = null;
};

const clearErrors = () => {
  chapterStore._setError(null);
  sceneStore._setError('details', null); // 清理场景相关的错误
};

const goBackToProject = () => {
  if (projectId.value) {
    router.push({name: 'ProjectWorkspace', params: {projectId: projectId.value}});
  } else {
    router.push({name: 'ProjectDashboard'});
  }
};

// 章节操作
const selectChapter = (chapterId) => {
  selectedChapterId.value = selectedChapterId.value === chapterId ? null : chapterId;
};

const openCreateChapterDialog = () => {
  isEditingChapter.value = false;
  // 设定默认 order 为当前最大 order + 1 或列表长度
  const maxOrder = chapters.value.reduce((max, ch) => Math.max(max, ch.order), -1);
  chapterFormData.value = {id: null, title: '', summary: '', order: maxOrder + 1};
  chapterDialogVisible.value = true;
  nextTick(() => {
    chapterFormRef.value?.clearValidate();
  });
};

const openEditChapterDialog = (chapter) => {
  isEditingChapter.value = true;
  chapterFormData.value = {...chapter}; // 浅拷贝编辑
  chapterDialogVisible.value = true;
  nextTick(() => {
    chapterFormRef.value?.clearValidate();
  });
};

const resetChapterForm = () => {
  chapterFormData.value = {id: null, title: '', summary: '', order: 0};
  chapterFormRef.value?.clearValidate();
};

const saveChapter = async () => {
  if (!chapterFormRef.value) return;
  try {
    await chapterFormRef.value.validate();
    isSavingChapter.value = true;
    if (isEditingChapter.value) {
      await chapterStore.updateChapter(chapterFormData.value.id, {
        title: chapterFormData.value.title,
        summary: chapterFormData.value.summary,
        order: chapterFormData.value.order,
      });
      ElMessage.success('章节已更新');
    } else {
      await chapterStore.createChapter(projectId.value, {
        title: chapterFormData.value.title,
        summary: chapterFormData.value.summary,
        order: chapterFormData.value.order,
      });
      ElMessage.success('章节已创建');
    }
    chapterDialogVisible.value = false;
  } catch (error) {
    if (error === false) {
      ElMessage.warning('请检查表单输入');
    } else {
      console.error('保存章节失败:', error);
      // 错误已在 store 处理
    }
  } finally {
    isSavingChapter.value = false;
  }
};

const confirmDeleteChapter = async (chapter) => {
  try {
    await ElMessageBox.confirm(
        `确定要删除章节 "${chapter.title || '此章节'}" 吗？章节下的所有场景也会被删除，此操作无法撤销！`,
        '确认删除章节',
        {confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning'}
    );
    await chapterStore.deleteChapter(chapter.id);
    ElMessage.success('章节及内部场景已删除');
    // 如果删除的是当前选中的章节，取消选中
    if (selectedChapterId.value === chapter.id) {
      selectedChapterId.value = null;
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除章节失败:', error);
      // 错误已在 store 处理
    }
  }
};

// 场景操作
const openCreateSceneDialog = (chapterId = null) => {
  const targetChapter = chapters.value.find(ch => ch.id === chapterId);
  const defaultOrder = targetChapter ? (targetChapter.scenes?.length || 0) : 0; // 默认放到末尾

  sceneFormData.value = {
    title: '',
    goal: '',
    chapter_id: chapterId, // 预设章节 ID
    order_in_chapter: defaultOrder
  };
  sceneDialogVisible.value = true;
  nextTick(() => {
    sceneFormRef.value?.clearValidate();
  });
};

const resetSceneForm = () => {
  sceneFormData.value = {title: '', goal: '', chapter_id: null, order_in_chapter: 0};
  sceneFormRef.value?.clearValidate();
};

const createScene = async () => {
  if (!sceneFormRef.value) return;
  try {
    await sceneFormRef.value.validate();
    isCreatingScene.value = true;
    await sceneStore.createScene({
      project_id: projectId.value,
      title: sceneFormData.value.title,
      goal: sceneFormData.value.goal,
      chapter_id: sceneFormData.value.chapter_id,
      order_in_chapter: sceneFormData.value.order_in_chapter,
    });
    ElMessage.success('场景已创建');
    sceneDialogVisible.value = false;
    // 如果创建到了当前选中的章节，可以保持展开，否则可能需要重新获取数据或手动更新
    // Store action 应该会处理好列表更新
  } catch (error) {
    if (error === false) {
      ElMessage.warning('请检查表单输入');
    } else {
      console.error('创建场景失败:', error);
      // 错误已在 store 处理
    }
  } finally {
    isCreatingScene.value = false;
  }
};

// --- 拖拽处理 ---
const onChapterDragEnd = async (event) => {
  console.log('Chapter drag end:', event);
  // `draggableChapters.value` 此时已经是拖拽后的顺序
  const newOrderedChapters = draggableChapters.value;
  // 批量更新 order
  const updates = newOrderedChapters.map((chapter, index) => ({
    id: chapter.id,
    updateData: {order: index} // 使用索引作为新的 order
  }));

  // 过滤掉 order 没有变化的章节，减少请求
  const changedUpdates = updates.filter(update => {
    const originalChapter = chapterStore.chapters.find(ch => ch.id === update.id);
    return originalChapter && originalChapter.order !== update.updateData.order;
  });

  if (changedUpdates.length > 0) {
    console.log('Updating chapter orders:', changedUpdates);
    // 使用 Promise.all 并行更新，或者按顺序更新
    try {
      await Promise.all(changedUpdates.map(u => chapterStore.updateChapter(u.id, u.updateData)));
      ElMessage.success('章节排序已更新');
      // 重新获取数据以保证同步，或者依赖 store action 的本地更新
      // await chapterStore.fetchChapters(projectId.value);
    } catch (error) {
      console.error('更新章节排序失败:', error);
      ElMessage.error('更新章节排序时发生错误');
      // 可能需要回滚本地更改或重新获取数据
      await chapterStore.fetchChapters(projectId.value);
    }
  }
};

const onSceneDragEnd = async (event) => {
  console.log('Scene drag end:', event);
  const {item, to, from, newIndex, oldIndex} = event;
  const sceneId = parseInt(item.dataset.sceneId || item.querySelector('.scene-item')?.dataset?.sceneId || item.getAttribute('data-scene-id'), 10); // 获取场景 ID 可能需要调整选择器

  if (isNaN(sceneId)) {
    console.error("无法获取拖拽场景的 ID", item);
    return;
  }

  const targetChapterIdStr = to.dataset.chapterId;
  const sourceChapterIdStr = from.dataset.chapterId;

  const targetChapterId = targetChapterIdStr === 'null' ? null : parseInt(targetChapterIdStr, 10);
  const sourceChapterId = sourceChapterIdStr === 'null' ? null : parseInt(sourceChapterIdStr, 10);


  // 获取目标列表 (章节内场景或未分配场景)
  let targetList;
  if (targetChapterId !== null) {
    const targetChapter = chapterStore.chapters.find(ch => ch.id === targetChapterId);
    targetList = targetChapter ? targetChapter.scenes : [];
  } else {
    targetList = sceneStore.unassignedScenes;
  }

  // 准备更新数据
  const updateData = {
    chapter_id: targetChapterId,
    previousChapterId: sourceChapterId,
    order_in_chapter: newIndex, // 新列表中的索引作为排序依据
  };

  console.log(`Moving scene ${sceneId} from chapter ${sourceChapterId} (index ${oldIndex}) to chapter ${targetChapterId} (index ${newIndex})`);
  console.log('Update data:', updateData);

  try {
    // 调用 store action 更新场景
    await sceneStore.updateScene(sceneId, updateData);

    // 如果在同一列表内移动，可能需要更新该列表中其他元素的 order_in_chapter
    // 如果跨列表移动，store action 应该已经处理了列表的增删
    // 为了简化，先依赖 store action 来处理列表状态更新
    // 但可能需要额外逻辑来更新同一章节内其他场景的 order_in_chapter

    // **精细化更新排序 (可选但推荐)**
    // 如果在同一个章节内移动，更新该章节内所有场景的 order_in_chapter
    if (targetChapterId !== null && targetChapterId === sourceChapterId) {
      const chapter = chapterStore.chapters.find(ch => ch.id === targetChapterId);
      if (chapter && chapter.scenes) {
        const sceneUpdates = chapter.scenes.map((scene, index) => ({
          id: scene.id,
          updateData: {
            previousChapterId: sourceChapterId,
            order_in_chapter: index
          }
        })).filter(u => {
          // 过滤掉未改变的和当前正在拖拽的元素（它的更新已在上面处理）
          // const originalScene = chapter.scenes.find(s => s.id === u.id); // 注意：此时 chapter.scenes 可能已被拖拽库修改
          return u.id !== sceneId; // 简单起见，更新所有其他场景的顺序
        });

        if (sceneUpdates.length > 0) {
          console.log("Updating sibling scene orders:", sceneUpdates);
          await Promise.all(sceneUpdates.map(u => sceneStore.updateScene(u.id, u.updateData)));
        }
      }
    } else if (targetChapterId !== null && targetChapterId !== sourceChapterId) {
      // 如果移动到新的章节，更新目标章节所有场景的 order_in_chapter
      const targetChapter = chapterStore.chapters.find(ch => ch.id === targetChapterId);
      if (targetChapter && targetChapter.scenes) {
        const sceneUpdates = targetChapter.scenes.map((scene, index) => ({
          id: scene.id,
          updateData: {
            previousChapterId: sourceChapterId,
            order_in_chapter: index
          }
        })).filter(u => u.id !== sceneId); // 更新除了刚拖入的之外的所有场景

        if (sceneUpdates.length > 0) {
          console.log("Updating target chapter scene orders:", sceneUpdates);
          await Promise.all(sceneUpdates.map(u => sceneStore.updateScene(u.id, u.updateData)));
        }
      }
    }


    ElMessage.success('场景位置已更新');
    // 重新获取数据或依赖 store action 更新UI
    // await fetchData(); // 可能导致闪烁，最好依赖 store 的响应式更新

  } catch (error) {
    console.error('更新场景位置失败:', error);
    ElMessage.error('更新场景位置时发生错误');
    // 拖拽失败，需要回滚 UI 或重新获取数据
    await fetchData(); // 强制刷新以恢复状态
  }
};


// --- Lifecycle Hooks ---
onMounted(() => {
  fetchData();
});

// 监听路由变化，如果 projectId 改变则重新加载
watch(projectId, (newId, oldId) => {
  if (newId !== oldId && newId) {
    fetchData();
  }
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

.box-card {
  margin-bottom: 20px;
  min-height: 400px; /* 给卡片一个最小高度 */
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header .el-icon {
  color: var(--el-text-color-secondary);
}

/* 章节列表 */
.chapter-list {
  padding-right: 5px; /* 防止滚动条遮挡 */
  max-height: calc(100vh - 250px); /* 限制最大高度，允许滚动 */
  overflow-y: auto;
}

.chapter-item {
  margin-bottom: 10px;
  border: 1px solid #e4e7ed;
  transition: border-color 0.3s;
}

.chapter-item.is-active {
  border-color: var(--el-color-primary);
}

.chapter-header {
  display: flex;
  align-items: center;
  padding: 10px;
  cursor: pointer;
  background-color: #f9f9f9;
  border-bottom: 1px solid #eee;
}

.chapter-item.is-active .chapter-header {
  background-color: #ecf5ff; /* Element Plus primary light */
}

.drag-handle-chapter {
  cursor: move;
  margin-right: 10px;
  color: #909399;
}

.chapter-title {
  flex-grow: 1;
  font-weight: bold;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chapter-actions {
  flex-shrink: 0;
  margin-left: 10px;
}

.chapter-actions .el-button {
  margin-left: 5px;
}

.chapter-scenes {
  padding: 10px;
  background-color: #fff;
}

/* 场景列表 (章节内和未分配) */
.scene-list-in-chapter, .unassigned-scene-list {
  min-height: 50px; /* 拖放区域最小高度 */
  padding: 5px;
  border-radius: 4px;
  background-color: #fdfdfd;
  border: 1px dashed #dcdfe6; /* 指示可拖放区域 */
}

.unassigned-scene-list {
  max-height: calc(100vh - 200px); /* 限制最大高度，允许滚动 */
  overflow-y: auto;
}

/* 场景项样式 (可以覆盖 SceneItem 内的) */
.draggable-scene-in-chapter, .draggable-scene-unassigned {
  background-color: white; /* 确保背景色 */
  /* margin-bottom: 5px; */ /* SceneItem 内部已有 margin */
}

/* 拖拽时的占位符样式 */
.ghost-chapter {
  opacity: 0.5;
  background: #c8ebfb;
  border: 1px dashed var(--el-color-primary);
}

.ghost-scene {
  opacity: 0.5;
  background: #f0f9eb; /* Element Plus success light */
  border: 1px dashed var(--el-color-success);
}

/* 拖拽中的元素样式 */
.dragging-scene {
  /* background-color: #fff !important; */
  /* box-shadow: 0 4px 8px rgba(0,0,0,0.1); */
  /* transform: scale(1.02); */
}


.empty-list {
  padding: 20px 0;
}

.empty-scene-list {
  padding: 15px;
  text-align: center;
}

/* 对话框样式 */
.dialog-footer {
  text-align: right;
}
</style>