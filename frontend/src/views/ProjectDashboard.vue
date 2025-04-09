<template>
  <div class="project-dashboard">
    <el-row justify="space-between" align="middle" class="dashboard-header">
      <el-col :span="12">
        <h1>我的项目</h1>
      </el-col>
      <el-col :span="12" style="text-align: right;">
        <el-button type="primary" @click="openCreateForm" :icon="Plus">
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
          <ProjectCard :project="project" @delete-project="handleDeleteProject"/>
        </el-col>
      </el-row>
    </div>

    <!-- Create/Edit Project Dialog -->
    <el-dialog
        v-model="isFormVisible"
        :title="formTitle"
        width="600px"
        :close-on-click-modal="false"
        @closed="resetFormState"
    >
      <ProjectForm
          ref="projectFormCompRef"
          :project-to-edit="null"
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
import {ElDialog, ElButton, ElRow, ElCol, ElAlert, ElEmpty, ElNotification, vLoading} from 'element-plus'; // Auto-imported likely
import {Plus} from '@element-plus/icons-vue'; // Import icon

const projectStore = useProjectStore();

const isFormVisible = ref(false);
const isSubmittingForm = ref(false);
const projectFormCompRef = ref(null); // Ref for the form component instance

const formTitle = computed(() => '创建新项目');

// Fetch projects when the component mounts
onMounted(() => {
  // Only fetch if the list isn't already populated or if there was a previous error
  if (projectStore.projectsList.length === 0 || projectStore.error) {
    projectStore.fetchProjects();
  }
});

// --- Form Handling ---
const openCreateForm = () => {
  isFormVisible.value = true;
};

const handleFormCancel = () => {
  isFormVisible.value = false;
};

const resetFormState = () => {
  // Called when dialog closes
  isSubmittingForm.value = false;
  // Optional: explicitly reset form if needed, though ProjectForm handles it internally now
  // projectFormCompRef.value?.resetForm();
}

const handleFormSubmit = async (formData) => {
  isSubmittingForm.value = true;
  try {
    const newProject = await projectStore.createProject(formData);
    isFormVisible.value = false;
    ElNotification({
      title: '成功',
      message: `项目 "${newProject.title}" 已创建`,
      type: 'success',
    });
  } catch (error) {
    // Error is already set in the store, but we can show a notification here
    ElNotification({
      title: '创建失败',
      message: projectStore.error || '无法创建项目，请稍后重试。',
      type: 'error',
    });
    // Keep the form open for correction
  } finally {
    isSubmittingForm.value = false;
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