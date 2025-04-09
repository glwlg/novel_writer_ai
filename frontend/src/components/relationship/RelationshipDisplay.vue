<template>
  <el-card shadow="hover" class="relationship-card">
    <template #header>
      <div class="card-header">
        <span>
          <el-icon><User /></el-icon> {{ relationship.character1_name }}
          <el-icon style="margin: 0 5px;"><Link /></el-icon>
          <el-icon><User /></el-icon> {{ relationship.character2_name }}
        </span>
        <div>
          <el-button type="primary" :icon="Edit" circle size="small" @click="onEdit" title="编辑关系"/>
          <el-button type="danger" :icon="Delete" circle size="small" @click="onDelete" title="删除关系"/>
        </div>
      </div>
    </template>
    <div>
      <el-descriptions :column="1" size="small" border>
        <el-descriptions-item label="关系类型">
          <el-tag :type="getTagType(relationship.relationship_type)">
            {{ getRelationshipTypeText(relationship.relationship_type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="关系描述" v-if="relationship.description">
          {{ relationship.description }}
        </el-descriptions-item>
         <el-descriptions-item label="创建时间">
            {{ formatDate(relationship.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间" v-if="relationship.updated_at">
            {{ formatDate(relationship.updated_at) }}
        </el-descriptions-item>
      </el-descriptions>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue';
import { ElCard, ElDescriptions, ElDescriptionsItem, ElButton, ElIcon, ElTag, ElMessageBox } from 'element-plus';
import { User, Link, Edit, Delete } from '@element-plus/icons-vue';
import { format } from 'date-fns'; // 用于格式化日期

// --- Props ---
const props = defineProps({
  relationship: {
    type: Object,
    required: true,
    // 建议添加校验器确保包含必要字段
    // validator: (value) => {
    //   return value && value.id && value.character1_id && value.character2_id && value.relationship_type && value.character1_name && value.character2_name && value.created_at;
    // }
  }
});

// --- Emits ---
const emit = defineEmits(['edit', 'delete']);

// --- 数据定义 ---
// 关系类型到中文文本和样式的映射
const RELATIONSHIP_TYPE_MAP = {
  'Friend': { text: '朋友', tagType: 'success' },
  'Enemy': { text: '敌人', tagType: 'danger' },
  'Family': { text: '家人', tagType: 'warning' },
  'Romantic': { text: '恋人', tagType: 'info' },
  'Ally': { text: '盟友', tagType: '' }, // 默认类型
  'Rival': { text: '对手', tagType: 'warning' },
  // 可以根据需要添加更多类型
};

// --- Computed ---
const getRelationshipTypeText = (type) => {
  return RELATIONSHIP_TYPE_MAP[type]?.text || type; // 如果未映射，显示原始类型
};

const getTagType = (type) => {
  return RELATIONSHIP_TYPE_MAP[type]?.tagType || 'primary'; // 默认 primary
}

// --- Methods ---
const onEdit = () => {
  emit('edit', props.relationship);
};

const onDelete = () => {
   ElMessageBox.confirm(
    `确定要删除角色 "${props.relationship.character1_name}" 与 "${props.relationship.character2_name}" 之间的关系吗？此操作不可撤销。`,
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
     emit('delete', props.relationship.id);
  }).catch(() => {
    // 用户取消删除
     console.log('取消删除');
  });
};

const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
        // 注意：后端返回的可能是带时区的 ISO 字符串，date-fns 会处理
        return format(new Date(dateString), 'yyyy-MM-dd HH:mm:ss');
    } catch (e) {
        console.error("日期格式化错误:", e);
        return dateString; // 返回原始字符串以防出错
    }
}

</script>

<style scoped>
.relationship-card {
  margin-bottom: 15px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-header span {
  font-weight: bold;
  display: flex;
  align-items: center;
}
.el-icon {
  margin-right: 5px;
}
</style>