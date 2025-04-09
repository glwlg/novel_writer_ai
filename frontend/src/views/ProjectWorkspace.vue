<template>
  <el-container class="project-workspace" v-loading="isLoading" :element-loading-text="loadingText">
    <el-alert
      v-if="showError"
      :title="'加载项目失败: ' + projectStore.error"
      type="error"
      show-icon
      class="error-alert"
      @close="projectStore._setError(null)"
      closable
    >
       <el-button link type="primary" @click="goBackToDashboard">返回项目列表</el-button>
       <el-button link type="warning" @click="retryFetch">重试</el-button>
    </el-alert>

    <template v-if="projectStore.currentProject && !projectStore.error">
      <el-aside width="220px" class="workspace-sidebar">
        <div class="project-title-sidebar">
          <h3>{{ projectStore.currentProject.title }}</h3>
          <!-- Add edit button for project metadata later if needed -->
        </div>
        <el-menu
          :default-active="activeMenu"
          class="workspace-menu"
          router
          :collapse="isCollapsed"
          @select="handleMenuSelect"
        >
           <!-- <el-menu-item @click="isCollapsed = !isCollapsed">
                <el-icon><Operation /></el-icon>
                <span>{{ isCollapsed ? '' : '收起/展开' }}</span>
            </el-menu-item> -->

           <el-sub-menu index="world-building">
             <template #title>
               <el-icon><Management /></el-icon>
               <span>世界观设定</span>
             </template>
             <el-menu-item :index="`/projects/${projectId}/characters`">
                <el-icon><User /></el-icon>角色管理
             </el-menu-item>
             <el-menu-item :index="`/projects/${projectId}/settings`">
                <el-icon><Collection /></el-icon>设定元素
             </el-menu-item>
             <el-menu-item :index="`/projects/${projectId}/relationships`">
                <el-icon><Connection /></el-icon>人物关系
             </el-menu-item>
           </el-sub-menu>

           <el-menu-item :index="`/projects/${projectId}/structure`">
             <el-icon><Tickets /></el-icon>
             <span>故事结构</span>
           </el-menu-item>

           <!-- Add Scene Editor entry point if needed directly here -->
           <!-- Or rely on navigation from Structure Editor -->

            <el-menu-item @click="goBackToDashboard" index="back">
                <el-icon><Back /></el-icon>
                <span>返回项目列表</span>
            </el-menu-item>

        </el-menu>
      </el-aside>

      <el-main class="workspace-main">
        <!-- Nested routes will render here -->
        <router-view v-slot="{ Component }">
          <keep-alive>
            <component :is="Component" :key="$route.fullPath" />
          </keep-alive>
        </router-view>
      </el-main>

    </template>
    <!-- Optional: Placeholder or message if no project is loaded but not loading/error -->
     <div v-else-if="!isLoading && !showError" class="workspace-placeholder">
         <!-- This state might not be reachable if loading handles initial state -->
         <el-empty description="未加载项目" />
      </div>
  </el-container>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router';
import { useProjectStore } from '@/store/project';
import {
    ElContainer, ElAside, ElMain, ElMenu, ElSubMenu, ElMenuItem, ElIcon, ElAlert, ElButton, ElEmpty, vLoading
} from 'element-plus'; // Auto-imported likely
import { Management, User, Collection, Connection, Tickets, Back, Operation } from '@element-plus/icons-vue'; // Import necessary icons

const route = useRoute();
const router = useRouter();
const projectStore = useProjectStore();

const isCollapsed = ref(false); // For potential sidebar collapse feature

// Extract projectId from route params reactively
const projectId = computed(() => {
    const id = route.params.projectId;
    return id ? parseInt(id, 10) : null;
});

// --- Loading and Error State ---
const isLoading = computed(() => projectStore.isLoadingDetails);
const showError = computed(() => !!projectStore.error && !projectStore.isLoadingDetails); // Show error only when not loading
const loadingText = computed(() =>
    projectStore.currentProject ? '正在加载项目组件...' : '正在加载项目详情...'
);


// --- Fetch Project Details ---
const fetchProjectData = async () => {
  if (projectId.value && projectId.value !== projectStore.currentProject?.id) {
    // Fetch details only if projectId is valid and different from the current one
    await projectStore.fetchProjectDetails(projectId.value);
     // If fetch fails, error state will be set in store
  } else if (!projectId.value) {
      // Handle invalid or missing projectId - redirect or show error
      console.error("Invalid Project ID");
      projectStore._setError({ message: '无效的项目ID' });
      // Optionally redirect back
      // router.replace({ name: 'ProjectDashboard' });
  }
};

// Fetch data when projectId changes or component mounts
watch(projectId, fetchProjectData, { immediate: true });

// Retry fetching data
const retryFetch = () => {
    projectStore._setError(null); // Clear previous error
    fetchProjectData();
}

// --- Navigation ---
const activeMenu = computed(() => {
    // Determine the active menu item based on the current route
    return route.path;
});

const handleMenuSelect = (index, indexPath) => {
  // console.log('Menu selected:', index, indexPath);
  // Navigation is handled by the `router` prop on el-menu
};

const goBackToDashboard = () => {
    router.push({ name: 'ProjectDashboard' }); // Adjust route name if different
}

// --- Cleanup ---
// Clear the current project details when navigating away from the workspace
// This is important to avoid showing stale data if the user navigates
// to another project or back to the dashboard.
const clearProjectOnLeave = () => {
    // Check if the navigation is away from *any* route under this project
    const isLeavingProjectScope = (to, from) => {
        const fromPrefix = `/projects/${from.params.projectId}`;
        const toPrefix = `/projects/${to.params.projectId}`;
        // Leaving if 'to' path doesn't start with the same project prefix
        // or if 'to' path doesn't have a projectId param (e.g., going to dashboard)
        return !to.path.startsWith(fromPrefix) || !to.params.projectId;
    };

    onBeforeRouteLeave((to, from) => {
        if (isLeavingProjectScope(to, from)) {
             console.log('Leaving project workspace scope, clearing project data.');
             projectStore.clearCurrentProject();
        }
    });
};

clearProjectOnLeave(); // Register the navigation guard

// Also clear on unmount, just in case (e.g., browser back/forward not caught by guard)
onBeforeUnmount(() => {
    // Check if the current route still belongs to this project context
    // If we are still within the project scope (e.g. just switching tabs within), don't clear.
    // This check might be redundant if onBeforeRouteLeave works reliably.
    // const currentProjectId = route.params.projectId ? parseInt(route.params.projectId, 10) : null;
    // if (projectStore.currentProject && projectStore.currentProject.id !== currentProjectId) {
    //     projectStore.clearCurrentProject();
    // }
    // Let's rely on the route guard primarily.
});

</script>

<style scoped>
.project-workspace {
  height: calc(100vh - 60px); /* Adjust based on your AppHeader height */
  /* border: 1px solid #eee; */
}

.workspace-sidebar {
  background-color: #f4f4f5; /* Lighter background */
  border-right: 1px solid #e4e7ed;
  overflow-y: auto;
}

.project-title-sidebar {
    padding: 15px;
    text-align: center;
    border-bottom: 1px solid #e4e7ed;
    margin-bottom: 10px;
    background-color: #ffffff;
}
.project-title-sidebar h3 {
    margin: 0;
    font-size: 1.1em;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}


.workspace-menu:not(.el-menu--collapse) {
  width: 220px; /* Ensure width matches el-aside */
   border-right: none; /* Remove default border */
}
.workspace-menu {
    background-color: transparent; /* Inherit from sidebar */
}

.el-menu-item.is-active {
  background-color: #e1eafc; /* A subtle active background */
  color: #409EFF; /* Element Plus primary color */
}
.el-menu-item:hover {
    background-color: #ebf1fd;
}

.workspace-main {
  padding: 20px;
  background-color: #ffffff;
  height: 100%; /* Ensure main area takes full height */
  overflow-y: auto; /* Allow scrolling within the main content */
}

.error-alert {
  margin: 20px;
  position: absolute; /* Position over the loading indicator if needed */
  z-index: 20;
  width: calc(100% - 40px); /* Adjust width */
}
.error-alert .el-button {
    margin-left: 10px;
}

.workspace-placeholder {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    width: 100%;
    color: #909399;
}
</style>