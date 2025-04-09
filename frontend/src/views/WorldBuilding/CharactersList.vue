<template>
  <el-container direction="vertical" class="character-list-container">
    <el-header height="auto" class="page-header">
      <h2>项目角色</h2>
      <el-button type="primary" :icon="Plus" @click="openCreateCharacterDialog">
        创建新角色
      </el-button>
    </el-header>

    <el-main>
      <el-alert
          v-if="error"
          :title="`错误: ${error}`"
          type="error"
          show-icon
          closable
          @close="characterStore._setError(null)"
      />

      <el-loading :visible="isLoading" text="正在加载角色...">

      </el-loading>
      <div v-if="!isLoading && !error && characters.length === 0" class="empty-state">
        <p>该项目下还没有角色。</p>
        <el-button type="text" @click="openCreateCharacterDialog">创建第一个？</el-button>
      </div>

      <el-row :gutter="20" v-else>
        <el-col
            v-for="character in characters"
            :key="character.id"
            :xs="24" :sm="12" :md="8" :lg="6" :xl="4"
            style="margin-bottom: 20px;"
        >
          <CharacterCard
              :character="character"
              @edit="openEditCharacterDialog"
              @delete="handleDeleteCharacterRequest"
          />
        </el-col>
      </el-row>
    </el-main>

    <!-- 创建/编辑 对话框 -->
    <el-dialog
        v-model="isFormDialogVisible"
        :title="dialogTitle"
        width="60%"
        :close-on-click-modal="false"
        @close="closeDialog"
        destroy-on-close
        draggable
    >
      <CharacterForm
          ref="characterFormRef"
          :initial-data="characterToEdit"
          @submit="handleFormSubmit"
          @cancel="closeDialog"
      />
    </el-dialog>

  </el-container>
</template>

<script setup>
import {ref, computed, onMounted, watch} from 'vue';
import {useRoute} from 'vue-router';
import {useCharacterStore} from '@/store/character'; // 根据需要调整路径
import CharacterCard from '@/components/character/CharacterCard.vue'; // 调整路径
import CharacterForm from '@/components/character/CharacterForm.vue'; // 调整路径
import {
  ElContainer,
  ElHeader,
  ElMain,
  ElButton,
  ElDialog,
  ElLoading,
  ElAlert,
  ElRow,
  ElCol,
  ElMessageBox,
  ElMessage
} from 'element-plus';
import {Plus} from '@element-plus/icons-vue';

const route = useRoute();
const characterStore = useCharacterStore();

const projectId = ref(null);
const isFormDialogVisible = ref(false);
const characterToEdit = ref(null); // 用于编辑的角色数据，为 null 表示创建模式
const characterFormRef = ref(null); // 用于访问表单方法的引用

// --- 计算属性 ---
const characters = computed(() => characterStore.characters);
const isLoading = computed(() => characterStore.isLoading);
const error = computed(() => characterStore.error);
const dialogTitle = computed(() => (characterToEdit.value ? '编辑角色' : '创建新角色'));

// --- 方法 ---
const loadCharacters = async () => {
  if (projectId.value) {
    console.log(`正在为项目 ID 获取角色: ${projectId.value}`);
    await characterStore.fetchCharacters(projectId.value);
  } else {
    console.warn("项目 ID 尚不可用。");
    characterStore.clearCharacters(); // 如果没有项目ID，则清除
  }
};

const openCreateCharacterDialog = () => {
  characterToEdit.value = null; // 确保是创建模式
  isFormDialogVisible.value = true;
};

const openEditCharacterDialog = (character) => {
  characterToEdit.value = {...character}; // 传递副本以避免直接修改 store
  isFormDialogVisible.value = true;
};

const closeDialog = () => {
  isFormDialogVisible.value = false;
  characterToEdit.value = null; // 清除编辑状态
  // 可选：如果需要，重置表单验证状态，但 destroy-on-close 通常能处理好
  // if (characterFormRef.value) {
  //     characterFormRef.value.resetFormValidation(); // 假设 CharacterForm 暴露了这个方法
  // }
};

const handleFormSubmit = async (formData) => {
  try {
    if (characterToEdit.value) {
      // 更新现有角色
      await characterStore.updateCharacter(characterToEdit.value.id, formData);
      ElMessage.success('角色更新成功！');
    } else {
      // 创建新角色
      // 确保 formData 中存在 project_id (由 store action 处理)
      await characterStore.createCharacter(projectId.value, formData);
      ElMessage.success('角色创建成功！');
    }
    closeDialog();
  } catch (err) {
    console.error('保存角色失败:', err);
    ElMessage.error(err.message || '保存角色失败。请检查详情。');
    // 错误已在 store action 中设置，这里可以显示更具体的反馈
  }
};

const handleDeleteCharacterRequest = (characterId) => {
  const character = characters.value.find(c => c.id === characterId);
  if (!character) return;

  ElMessageBox.confirm(
      `您确定要删除角色 “${character.name}” 吗？此操作无法撤销。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
  ).then(async () => {
    // 已确认
    try {
      await characterStore.deleteCharacter(characterId);
      ElMessage.success(`角色 “${character.name}” 删除成功。`);
    } catch (err) {
      console.error('删除角色失败:', err);
      ElMessage.error(err.message || '删除角色失败。');
    }
  }).catch(() => {
    // 已取消
    ElMessage.info('删除已取消。');
  });
};


// --- 生命周期钩子 ---
onMounted(() => {
  const idFromRoute = parseInt(route.params.projectId, 10);
  if (!isNaN(idFromRoute)) {
    projectId.value = idFromRoute;
    loadCharacters();
  } else {
    console.error("路由中的项目 ID 无效:", route.params.projectId);
    characterStore._setError("无效的项目 ID。");
  }
});

// 监听路由变化，如果用户可以在工作区内导航到不同项目
watch(
    () => route.params.projectId,
    (newId) => {
      const idFromRoute = parseInt(newId, 10);
      if (!isNaN(idFromRoute) && idFromRoute !== projectId.value) {
        projectId.value = idFromRoute;
        characterStore.clearCharacters(); // 加载新角色前清除旧的
        loadCharacters();
      } else if (isNaN(idFromRoute)) {
        console.error("路由变化中的项目 ID 无效:", newId);
        characterStore._setError("无效的项目 ID。");
        characterStore.clearCharacters();
        projectId.value = null;
      }
    }
);

</script>

<style scoped>
.character-list-container {
  padding: 20px;
  height: 100%; /* 确保容器占满高度 */
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--el-border-color-light);
  padding-bottom: 15px;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

.el-loading {
  min-height: 200px; /* 确保加载状态有一定空间 */
}

.empty-state {
  text-align: center;
  color: var(--el-text-color-secondary);
  padding: 40px 0;
}
</style>