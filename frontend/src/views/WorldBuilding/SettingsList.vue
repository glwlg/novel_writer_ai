<template>
  <div class="settings-list-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>世界观设定管理</span>
          <el-button type="primary" :icon="Plus" @click="openCreateDialog">
            添加新设定
          </el-button>
        </div>
      </template>

      <!-- 加载状态 -->
      <el-skeleton :rows="5" animated v-if="isLoading" />

      <!-- 错误提示 -->
      <el-alert
        v-else-if="error"
        :title="`加载设定失败: ${error}`"
        type="error"
        show-icon
        :closable="false"
      />

      <!-- 设定列表 -->
      <div v-else-if="settings.length > 0" class="settings-grid">
         <SettingCard
           v-for="setting in settings"
           :key="setting.id"
           :setting="setting"
           @edit="openEditDialog"
           @delete="handleDeleteSetting"
         />
      </div>

      <!-- 空状态 -->
      <el-empty v-else description="暂无设定元素，快去添加吧！" />

    </el-card>

    <!-- 创建/编辑 对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditMode ? '编辑设定' : '创建新设定'"
      width="60%"
      :close-on-click-modal="false"
      :before-close="handleDialogClose"
    >
      <SettingForm
        v-if="dialogVisible"
        ref="settingFormInstance"
        :initial-data="currentEditingSetting"
        :is-edit-mode="isEditMode"
        @submit="handleFormSubmit"
        @cancel="handleDialogClose"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useSettingStore } from '@/store/setting'; // 确认路径正确
import SettingCard from '@/components/setting/SettingCard.vue'; // 确认路径正确
import SettingForm from '@/components/setting/SettingForm.vue'; // 确认路径正确
import { ElCard, ElButton, ElDialog, ElSkeleton, ElAlert, ElEmpty, ElMessage, ElMessageBox } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';

// --- Hooks ---
const route = useRoute();
const settingStore = useSettingStore();

// --- Refs ---
const dialogVisible = ref(false); // 控制对话框显示
const isEditMode = ref(false); // 标记是创建还是编辑模式
const currentEditingSetting = ref(null); // 当前正在编辑的设定数据
const settingFormInstance = ref(null); // 对 SettingForm 组件实例的引用 (如果需要调用其内部方法)

// --- Computed Properties ---
const projectId = computed(() => parseInt(route.params.projectId, 10)); // 从路由获取项目 ID
const settings = computed(() => settingStore.settings);
const isLoading = computed(() => settingStore.isLoading);
const error = computed(() => settingStore.error);

// --- Methods ---
// 获取设定列表
const fetchSettingsData = async () => {
  if (projectId.value) {
    await settingStore.fetchSettings(projectId.value);
    if (settingStore.error) {
        ElMessage.error(`加载设定列表失败: ${settingStore.error}`);
    }
  } else {
      console.warn("SettingsList: Project ID is missing.");
      settingStore.clearSettings(); // 清空旧数据
  }
};

// 打开创建对话框
const openCreateDialog = () => {
  isEditMode.value = false;
  currentEditingSetting.value = null; // 清空编辑数据
  dialogVisible.value = true;
};

// 打开编辑对话框
const openEditDialog = (settingId) => {
  const settingToEdit = settings.value.find(s => s.id === settingId);
  if (settingToEdit) {
    isEditMode.value = true;
    // 传递普通对象副本，避免直接修改 store 状态
    currentEditingSetting.value = { ...settingToEdit };
    dialogVisible.value = true;
  } else {
    ElMessage.warning('找不到要编辑的设定');
  }
};

// 处理表单提交 (来自 SettingForm 的 'submit' 事件)
const handleFormSubmit = async (formData) => {
  try {
    if (isEditMode.value && currentEditingSetting.value) {
      // --- 编辑模式 ---
      // 准备更新数据 (只包含可更新字段)
      const updateData = {
          name: formData.name,
          element_type: formData.element_type,
          description: formData.description,
      };
      await settingStore.updateSetting(currentEditingSetting.value.id, updateData);
      ElMessage.success('设定更新成功！');
    } else {
      // --- 创建模式 ---
      // 准备创建数据 (包含 project_id)
      const createData = {
          ...formData,
          project_id: projectId.value, // 从 computed 属性获取
      };
      await settingStore.createSetting(projectId.value, createData);
      ElMessage.success('设定创建成功！');
    }
    dialogVisible.value = false; // 关闭对话框
    // (可选) 可以在这里重新获取数据，如果 store 更新不及时
    // await fetchSettingsData();
  } catch (err) {
      const action = isEditMode.value ? '更新' : '创建';
      console.error(`${action}设定失败:`, err);
      // 错误信息可能在 store 的 error 状态中，或者从抛出的 err 中获取
      const errorMsg = settingStore.error || err.message || `设定${action}失败，请稍后重试`;
      ElMessage.error(errorMsg);
      // 不关闭对话框，让用户可以修改重试
  }
};

// 处理删除设定按钮点击 (来自 SettingCard 的 'delete' 事件)
const handleDeleteSetting = (settingId) => {
   const settingToDelete = settings.value.find(s => s.id === settingId);
   if (!settingToDelete) return;

   ElMessageBox.confirm(
     `确定要删除设定 "${settingToDelete.name}" 吗？此操作不可撤销。`,
     '确认删除',
     {
       confirmButtonText: '确定删除',
       cancelButtonText: '取消',
       type: 'warning',
     }
   )
     .then(async () => {
       // 用户确认删除
       try {
         await settingStore.deleteSetting(settingId);
         ElMessage.success('设定删除成功！');
         // Store 会自动更新列表
       } catch (err) {
         console.error('删除设定失败:', err);
         const errorMsg = settingStore.error || err.message || '删除设定失败，请稍后重试';
         ElMessage.error(errorMsg);
       }
     })
     .catch(() => {
       // 用户取消删除
       ElMessage.info('已取消删除');
     });
};

// 处理对话框关闭 (点击关闭按钮或遮罩层)
const handleDialogClose = (done) => {
  // 重置状态
  currentEditingSetting.value = null;
  isEditMode.value = false;
  if (typeof done === 'function') {
      done(); // Element Plus 的回调
  } else {
      dialogVisible.value = false; // 手动关闭
  }
};

// --- Watchers ---
// 监听项目 ID 变化，重新加载数据
watch(projectId, (newId, oldId) => {
  if (newId !== oldId && newId) {
    fetchSettingsData();
  }
}, { immediate: false }); // 不在初始渲染时触发，让 onMounted 处理

// --- Lifecycle Hooks ---
onMounted(() => {
  // 组件挂载时加载数据
  fetchSettingsData();
});

// --- Cleanup ---
// (可选) 在 onUnmounted 中清除 store 数据或取消请求
// import { onUnmounted } from 'vue';
// onUnmounted(() => {
//   settingStore.clearSettings();
// });

</script>

<style scoped>
.settings-list-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.settings-grid {
  /* 可以使用 Grid 或 Flex 布局展示 Card */
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); /* 响应式网格 */
  gap: 16px;
}

/* 当只有一个项目时，防止它拉伸过宽 (可选) */
.settings-grid:only-child {
    grid-template-columns: minmax(300px, 500px);
    justify-content: center; /* 或 start */
}


/* 确保对话框内的表单有合适的间距 */
:deep(.el-dialog__body) {
  padding: 20px 30px;
}
</style>