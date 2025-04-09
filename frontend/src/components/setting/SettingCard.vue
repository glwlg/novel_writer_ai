<template>
  <el-card shadow="hover" class="setting-card">
    <template #header>
      <div class="card-header">
        <span>
            <el-tag :type="getTagType(setting.element_type)" effect="light" size="small" style="margin-right: 8px;">
                {{ getSettingTypeLabel(setting.element_type) }}
            </el-tag>
            <span class="setting-name">{{ setting.name }}</span>
        </span>
        <div class="card-actions">
          <el-tooltip content="编辑" placement="top">
            <el-button type="primary" :icon="Edit" circle size="small" @click="handleEdit"/>
          </el-tooltip>
          <el-tooltip content="删除" placement="top">
            <el-button type="danger" :icon="Delete" circle size="small" @click="handleDelete"/>
          </el-tooltip>
        </div>
      </div>
    </template>
    <div class="setting-description" v-if="setting.description">
      {{ truncateDescription(setting.description) }}
    </div>
    <div class="setting-description" v-else>
      <el-text type="info" size="small">暂无描述</el-text>
    </div>
    <!-- (可选) 显示创建/更新时间 -->
    <div class="setting-meta">
      <el-text type="info" size="small">创建于: {{ formatDate(setting.created_at) }}</el-text>
      <el-text type="info" size="small" v-if="setting.updated_at" style="margin-left: 10px;">更新于:
        {{ formatDate(setting.updated_at) }}
      </el-text>
    </div>
  </el-card>
</template>

<script setup>
import {ElCard, ElButton, ElTooltip, ElTag, ElText} from 'element-plus';
import {Edit, Delete} from '@element-plus/icons-vue';
import {format} from 'date-fns'; // 用于格式化日期

// --- Props ---
const props = defineProps({
  setting: {
    type: Object,
    required: true,
    // 校验器 (可选，增加健壮性)
    validator: (value) => {
      return value && typeof value.id === 'number' && typeof value.name === 'string';
    }
  },
});

// --- Emits ---
const emit = defineEmits(['edit', 'delete']);

// --- Data / Refs ---
// 设定类型及其对应的标签颜色 (可以根据需要调整)
const settingTypeTags = {
  'Location': 'success',
  'Item': 'warning',
  'Concept': 'info',
  'Organization': 'primary',
  'Event': 'danger',
  'Other': '', // 默认
};

// 设定类型中文映射 (与 Form 组件保持一致)
const settingTypeLabels = {
  'Location': '地点',
  'Item': '物品',
  'Concept': '概念',
  'Faction': '阵营/组织',
  'Character Trait': '角色特质',
  'World Rule': '世界规则',
  'Lore': '背景传说',
  'Technology': '技术设定',
  'Magic System': '魔法体系',
  'Other': '其他',
};

// --- Computed / Methods ---
// 获取设定类型的标签颜色
const getTagType = (type) => {
  return settingTypeTags[type] || ''; // 返回默认或空
};

// 获取设定类型的中文标签
const getSettingTypeLabel = (type) => {
  return settingTypeLabels[type] || type; // 如果找不到映射，返回原始值
};

// 截断描述文本
const truncateDescription = (text, maxLength = 100) => {
  if (!text) return '';
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
};

// 格式化日期 (需要安装 date-fns: npm install date-fns)
const formatDate = (dateString) => {
  if (!dateString) return '';
  try {
    return format(new Date(dateString), 'yyyy-MM-dd HH:mm');
  } catch (error) {
    console.error('日期格式化错误:', error);
    return dateString; // 返回原始字符串以防出错
  }
};

// 处理编辑按钮点击
const handleEdit = () => {
  emit('edit', props.setting.id); // 传递 setting ID
};

// 处理删除按钮点击
const handleDelete = () => {
  emit('delete', props.setting.id); // 传递 setting ID
};
</script>

<style scoped>
.setting-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.setting-name {
  font-weight: bold;
  margin-left: 5px; /* 增加标签和名称的间距 */
}

.card-actions {
  display: flex;
  gap: 8px; /* 按钮间距 */
}

.setting-description {
  font-size: 14px;
  color: var(--el-text-color-regular);
  line-height: 1.5;
  margin-bottom: 10px; /* 描述和元数据间距 */
}

.setting-meta {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 8px;
  text-align: right;
}
</style>