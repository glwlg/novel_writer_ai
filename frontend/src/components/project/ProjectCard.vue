<template>
  <el-card class="project-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <el-row>
          <span>{{ project.title }}</span>
        </el-row>
        <el-row class="card-header-btn">
          <div>
            <el-button type="primary" link @click="goToWorkspace">
              <el-icon>
                <View/>
              </el-icon>
              打开
            </el-button>
            <el-button type="primary" link @click="handleEdit">
              <el-icon>
                <View/>
              </el-icon>
              编辑
            </el-button>
            <el-button type="danger" link @click="confirmDelete">
              <el-icon>
                <Delete/>
              </el-icon>
              删除
            </el-button>
          </div>
        </el-row>
      </div>
    </template>
    <div class="project-logline" v-if="project.logline">
      {{ project.logline }}
    </div>
    <div class="project-meta" v-if="project.created_at">
      创建于: {{ formattedDate(project.created_at) }}
    </div>
    <div class="project-meta" v-if="project.updated_at">
      更新于: {{ formattedDate(project.updated_at) }}
    </div>
  </el-card>
</template>

<script setup>
import {defineProps, defineEmits} from 'vue';
import {useRouter} from 'vue-router';
import {ElMessageBox, ElNotification} from 'element-plus';
import {View, Delete} from '@element-plus/icons-vue'; // Import icons
import {format} from 'date-fns';

const props = defineProps({
  project: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['delete', 'edit']);

const router = useRouter();

const handleEdit = () => {
  emit('edit', props.project.id);
};
const goToWorkspace = () => {
  if (props.project && props.project.id) {
    router.push({name: 'StructureEditor', params: {projectId: props.project.id}});
  }
};

const confirmDelete = () => {
  ElMessageBox.confirm(
      `确定要删除项目 "${props.project.title}" 吗？此操作将删除项目及其所有相关数据（角色、设定、章节、场景等），且不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
  )
      .then(() => {
        emit('delete', props.project.id);
      })
      .catch(() => {
        // User cancelled
        ElNotification({
          title: '已取消',
          message: '删除操作已取消',
          type: 'info',
          duration: 2000,
        });
      });
};

const formattedDate = (dateString) => {
  if (!dateString) return '';
  try {
    return format(new Date(dateString), 'yyyy-MM-dd HH:mm');
  } catch (e) {
    console.error("Error formatting date:", e);
    return dateString; // Fallback to original string
  }
};
</script>

<style scoped>
.project-card {
  margin-bottom: 20px;
}

.card-header {
  /* display: flex; */
  justify-content: space-between;
  align-items: center;
}

.card-header-btn {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  padding: 5px;
}

.card-header span {
  font-weight: bold;
}

.project-logline {
  color: #606266;
  font-size: 0.9em;
  margin-bottom: 10px;
  white-space: pre-wrap; /* Preserve line breaks if any */
  word-break: break-word;
}

.project-meta {
  font-size: 0.8em;
  color: #909399;
  margin-top: 5px;
}

.el-button + .el-button {
  margin-left: 8px; /* Add some spacing between buttons */
}

.el-icon {
  margin-right: 4px;
}
</style>