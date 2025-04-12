<template>
  <div class="project-dashboard">
    <el-row justify="space-between" align="middle" class="dashboard-header">
      <el-col :span="12">
        <h1>我的项目</h1>
      </el-col>
      <el-col :span="12" style="text-align: right;">
        <el-button type="primary" @click="openCreateDialog" :icon="Plus">
          创建新项目
        </el-button>
      </el-col>
    </el-row>

    <el-alert
        v-if="projectStore.error && !projectStore.isLoadingList"
        :title="'加载项目列表失败: ' + projectStore.error"
        type="error"
        show-icon
        closable
        @close="projectStore._setError(null)"
        style="margin-bottom: 20px;"
    />

    <div v-loading="projectStore.isLoadingList" element-loading-text="正在加载项目列表...">
      <div v-if="!projectStore.isLoadingList && projectStore.projectsList.length === 0 && !projectStore.error"
           class="empty-state">
        <el-empty description="还没有任何项目，点击“创建新项目”开始吧！"/>
      </div>

      <el-row :gutter="20" v-else>
        <el-col
            v-for="project in projectStore.projectsList"
            :key="project.id"
            :xs="24" :sm="12" :md="8" :lg="6"
        >
          <ProjectCard :project="project" @edit="openEditDialog" @delete="handleDeleteProject"/>
        </el-col>
      </el-row>
    </div>

    <!-- Create/Edit Project Dialog -->
    <el-dialog
        v-model="dialogVisible"
        :title="formTitle"
        width="600px"
        :close-on-click-modal="false"
        @closed="resetFormState"
    >
      <ProjectForm
          ref="projectFormCompRef"
          :project-to-edit="currentEditingProject"
          :is-submitting="isSubmittingForm"
          @submit="handleFormSubmit"
          @cancel="handleFormCancel"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import {ref, onMounted, computed} from 'vue';
import {useProjectStore} from '@/store/project';
import ProjectCard from '@/components/project/ProjectCard.vue';
import ProjectForm from '@/components/project/ProjectForm.vue';
import {ElDialog, ElButton, ElRow, ElCol, ElAlert, ElEmpty, ElNotification, vLoading, ElMessage} from 'element-plus'; // Auto-imported likely
import {Plus} from '@element-plus/icons-vue'; // Import icon

const projectStore = useProjectStore();

const dialogVisible = ref(false);
const isSubmittingForm = ref(false);
const isEditMode = ref(false);
const projectFormCompRef = ref(null); // Ref for the form component instance
const currentEditingProject = ref(null); // 当前正在编辑的项目

// --- Computed Properties ---
const projects = computed(() => projectStore.projectsList);

const formTitle = computed(() => '创建新项目');

// Fetch projects when the component mounts
onMounted(() => {
  // Only fetch if the list isn't already populated or if there was a previous error
  if (projectStore.projectsList.length === 0 || projectStore.error) {
    projectStore.fetchProjects();
  }
});

// 打开创建对话框
const openCreateDialog = () => {
  isEditMode.value = false;
  currentEditingProject.value = null; // 清空编辑数据
  dialogVisible.value = true;
};

// 打开编辑对话框
const openEditDialog = (projectId) => {
  const projectToEdit = projects.value.find(s => s.id === projectId);
  if (projectToEdit) {
    isEditMode.value = true;
    // 传递普通对象副本，避免直接修改 store 状态
    currentEditingProject.value = {...projectToEdit};
    dialogVisible.value = true;
  } else {
    ElMessage.warning('找不到要编辑的项目');
  }
};

const handleFormCancel = () => {
  dialogVisible.value = false;
};

const resetFormState = () => {
  // Called when dialog closes
  isSubmittingForm.value = false;
}
// 处理表单提交 (来自 SettingForm 的 'submit' 事件)
const handleFormSubmit = async (formData) => {
  try {
    if (isEditMode.value && currentEditingProject.value) {
      // --- 编辑模式 ---
      // 准备更新数据 (只包含可更新字段)
      const updateData = {
        title: formData.title,
        logline: formData.logline,
        global_synopsis: formData.global_synopsis,
        style: formData.style,
      };
      await projectStore.updateProject(currentEditingProject.value.id, updateData);
      ElMessage.success('设定更新成功！');
    } else {
      // --- 创建模式 ---
      await projectStore.createProject(formData);
      ElMessage.success('项目创建成功！');
    }
    dialogVisible.value = false; // 关闭对话框
    // (可选) 可以在这里重新获取数据，如果 store 更新不及时
    // await fetchSettingsData();
  } catch (err) {
    const action = isEditMode.value ? '更新' : '创建';
    console.error(`${action}项目失败:`, err);
    // 错误信息可能在 store 的 error 状态中，或者从抛出的 err 中获取
    const errorMsg = projectStore.error || err.message || `项目${action}失败，请稍后重试`;
    ElMessage.error(errorMsg);
    // 不关闭对话框，让用户可以修改重试
  }
};

// --- Deletion Handling ---
const handleDeleteProject = async (projectId) => {
  try {
    // Confirmation is handled within ProjectCard
    const deletedProject = await projectStore.deleteProject(projectId);
    console.log(deletedProject);
    ElNotification({
      title: '已删除',
      message: `项目 "${deletedProject.title}" 已成功删除`,
      type: 'success',
    });
  } catch (error) {
    ElNotification({
      title: '删除失败',
      message: projectStore.error || '无法删除项目，请稍后重试。',
      type: 'error',
    });
  }
};
</script>

<style scoped>
.project-dashboard {
  padding: 20px;
}

.dashboard-header {
  margin-bottom: 30px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px; /* Ensure it takes some space */
  color: #909399;
}

/* Ensure loading covers the content area */
.el-loading-mask {
  z-index: 10; /* Ensure it's above cards if they render momentarily */
}

.el-loading-spinner {
  top: 40%; /* Adjust vertical position */
}
</style>