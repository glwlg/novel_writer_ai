<template>
  <div class="relationships-list-container" v-loading="relationshipStore.isLoading">
    <el-card>
        <template #header>
            <div class="card-header">
                <span>人物关系管理</span>
                 <el-button type="primary" :icon="Plus" @click="openCreateForm">添加关系</el-button>
            </div>
        </template>

        <!-- 筛选区域 (可选) -->
         <el-row :gutter="20" style="margin-bottom: 20px;">
             <el-col :span="8">
                <el-select
                    v-model="filterCharacterId"
                    placeholder="按角色筛选关系"
                    clearable
                    filterable
                    style="width: 100%;"
                    @change="handleFilterChange"
                >
                 <el-option label="所有角色" :value="null"></el-option>
                 <el-option
                    v-for="char in characterStore.characters"
                    :key="char.id"
                    :label="char.name"
                    :value="char.id"
                />
                </el-select>
             </el-col>
             <!-- 可以添加更多筛选条件 -->
         </el-row>

        <!-- 错误提示 -->
        <el-alert
            v-if="relationshipStore.error"
            :title="'加载关系列表失败: ' + relationshipStore.error"
            type="error"
            show-icon
            style="margin-bottom: 15px;"
            :closable="false"
         />

        <!-- 关系列表 -->
        <div v-if="!relationshipStore.isLoading && displayedRelationships.length === 0 && !relationshipStore.error">
            <el-empty description="暂无人物关系，快去添加吧！"></el-empty>
        </div>
        <div v-else class="relationship-list">
             <RelationshipDisplay
                v-for="rel in displayedRelationships"
                :key="rel.id"
                :relationship="rel"
                @edit="openEditForm"
                @delete="handleDeleteRelationship"
             />
        </div>

         <!-- 分页 (如果需要) -->
         <!--
         <el-pagination
             v-if="totalRelationships > pageSize"
             style="margin-top: 20px; justify-content: flex-end;"
             layout="prev, pager, next, total"
             :total="totalRelationships"
             :page-size="pageSize"
             :current-page="currentPage"
             @current-change="handlePageChange"
         />
         -->

    </el-card>

    <!-- 创建/编辑关系的对话框 -->
    <RelationshipForm
        v-if="dialogVisible"
        :visible="dialogVisible"
        :initial-data="editingRelationship"
        :project-id="projectId"
        :characters="characterStore.characters"
        @update:visible="dialogVisible = $event"
        @success="handleFormSuccess"
    />

  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { ElCard, ElButton, ElIcon, ElRow, ElCol, ElSelect, ElOption, ElAlert, ElEmpty, ElPagination, ElLoadingDirective as vLoading, ElMessage } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';
import { useRelationshipStore } from '@/store/relationship';
import { useCharacterStore } from '@/store/character';
import RelationshipDisplay from '@/components/relationship/RelationshipDisplay.vue'; // 调整路径
import RelationshipForm from '@/components/relationship/RelationshipForm.vue'; // 调整路径

// --- Stores ---
const relationshipStore = useRelationshipStore();
const characterStore = useCharacterStore(); // 需要角色列表用于筛选和表单

// --- Router ---
const route = useRoute();
const projectId = computed(() => route.params.projectId);

// --- Refs ---
const dialogVisible = ref(false); // 控制表单对话框的显示
const editingRelationship = ref(null); // 存储正在编辑的关系数据，null 表示创建模式
const filterCharacterId = ref(null); // 筛选用的角色 ID

// --- Pagination (如果需要) ---
// const currentPage = ref(1);
// const pageSize = ref(10); // 或者从配置读取
// const totalRelationships = computed(() => relationshipStore.relationships.length); // 简单的总数，如果后端分页需要修改

// --- Computed ---
// 使用 store 的 getter 来获取带名字的关系列表
const displayedRelationships = computed(() => relationshipStore.relationshipsWithNames);

// 如果需要前端分页
// const paginatedRelationships = computed(() => {
//   const start = (currentPage.value - 1) * pageSize.value;
//   const end = start + pageSize.value;
//   return displayedRelationships.value.slice(start, end);
// });

// --- Methods ---
const fetchData = async () => {
  if (!projectId.value) return;
  // 每次获取数据前，清除之前的状态可能更好
  // relationshipStore.clearRelationships();
  // characterStore.clearCharacters(); // 假设角色列表也在项目切换时获取

  // 确保角色列表已加载，因为表单和显示都需要
  if (characterStore.characters.length === 0) {
      try {
          await characterStore.fetchCharacters(projectId.value);
      } catch (err) {
          ElMessage.error("加载角色列表失败，无法进行关系管理。");
          return; // 如果角色加载失败，阻止关系加载
      }
  }

  // 获取关系列表，传入筛选参数
  await relationshipStore.fetchRelationships(projectId.value, filterCharacterId.value);
};

const openCreateForm = () => {
  if (characterStore.characters.length < 2) {
       ElMessage.warning("请先创建至少两个角色才能添加关系。");
       return;
  }
  editingRelationship.value = null; // 清空编辑数据，表示创建
  dialogVisible.value = true;
};

const openEditForm = (relationship) => {
  editingRelationship.value = relationship; // 设置要编辑的数据
  dialogVisible.value = true;
};

const handleDeleteRelationship = async (relationshipId) => {
  try {
    await relationshipStore.deleteRelationship(relationshipId);
    ElMessage.success('关系删除成功！');
    // 可选：如果删除了当前筛选角色的关系，可能需要重新思考筛选逻辑，但通常保留当前筛选即可
    // 如果使用了分页，可能需要调整当前页码
    // if (paginatedRelationships.value.length === 0 && currentPage.value > 1) {
    //     currentPage.value--;
    // }
  } catch (err) {
     // 错误消息已由 store 的 _setError 处理
     // ElMessage.error(relationshipStore.error || '删除失败');
     console.error("删除关系时出错:", err);
  }
};

const handleFormSuccess = () => {
  dialogVisible.value = false; // 关闭对话框
  // 无需手动刷新列表，因为 store 的 action 应该已经更新了 state
  // 如果 store 没有响应式更新，则需要手动调用 fetchData()
  // fetchData();
};

const handleFilterChange = () => {
    // currentPage.value = 1; // 筛选变化时回到第一页
    fetchData(); // 重新获取数据
}

// const handlePageChange = (newPage) => {
//     currentPage.value = newPage;
//     // 如果是后端分页，这里需要调用 fetchData 并传入分页参数
// }

// --- Lifecycle Hooks ---
onMounted(() => {
  fetchData();
});

// 监听项目 ID 变化，重新加载数据
watch(projectId, (newId, oldId) => {
  if (newId && newId !== oldId) {
    filterCharacterId.value = null; // 重置筛选
    // currentPage.value = 1; // 重置页码
    fetchData();
  } else if (!newId) {
      // 如果项目ID无效，清空数据
      relationshipStore.clearRelationships();
      characterStore.clearCharacters(); // 假设角色也清空
  }
});

</script>

<style scoped>
.relationships-list-container {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.relationship-list {
  /* 可以添加样式，比如 grid 布局 */
  /* display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px; */
}
</style>