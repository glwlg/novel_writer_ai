<template>
  <el-card shadow="never" class="chapter-item" :class="{ 'is-active': isSelected }">
    <div class="chapter-header" @click="handleSelect">
      <!-- Display chapter order, title, and scene count -->
      <span class="chapter-title">
        {{ '第' + (chapter.order + 1) + '章 ' + (chapter.title || '未命名章节') }}
        ({{ chapter.scenes?.length || 0 }} 场景)
      </span>
      <div class="chapter-actions">
        <!-- Edit Button -->
        <el-tooltip content="编辑章节" placement="top">
          <el-button link type="primary" :icon="Edit" @click.stop="handleEdit" size="small"/>
        </el-tooltip>
        <!-- Generate Scenes Button -->
        <el-tooltip :content="chapter.scenes?.length > 0 ? '请先删除已有场景才能重新生成' : '生成场景'" placement="top">
          <el-button :disabled="!!chapter.scenes?.length" link type="success" :icon="MagicStick"
                     @click.stop="handleGenerate" size="small"/>
        </el-tooltip>
        <el-tooltip content="删除章节" placement="top">
          <div>
            <el-popconfirm
                :title="`确定删除章节 '${chapter?.title}' 吗？章节下的所有场景也会被删除！`"
                confirm-button-text="确认删除"
                cancel-button-text="取消"
                @confirm="handleDelete"
                width="300"
                ref="chapterDeleteConfirmRef"
            >
              <template #reference>
                <el-button link type="danger" :icon="Delete" @click.stop size="small"/>
              </template>
            </el-popconfirm>
          </div>
        </el-tooltip>
      </div>
    </div>
    <!-- Scene List (conditionally shown) -->
    <el-collapse-transition>
      <div v-show="isSelected" class="chapter-scenes">
        <div v-if="!chapter.scenes || chapter.scenes.length === 0" class="empty-scene-list">
          <el-text size="small" type="info">暂无场景，点击上方 '生成场景' 按钮创建</el-text>
        </div>
        <div v-else class="scene-list-in-chapter">
          <!-- Ensure SceneItem is imported -->
          <SceneItem v-for="scene in sortedScenes" :key="scene.id" :scene="scene"
                     @generate="handleSceneContentGenerate"
                     class="scene-item-display"/>
        </div>
      </div>
    </el-collapse-transition>
  </el-card>
</template>

<script setup>
import {computed} from 'vue';
import {ElCard, ElButton, ElTooltip, ElCollapseTransition, ElText, ElPopconfirm} from 'element-plus';
import {Delete, Edit, MagicStick} from '@element-plus/icons-vue';
import SceneItem from '@/components/scene/SceneItem.vue'; // Make sure path is correct

// --- Props ---
const props = defineProps({
  chapter: {
    type: Object,
    required: true,
    default: () => ({id: null, title: '', summary: '', order: 0, scenes: [], content: null}) // Add scenes & content default
  },
  isSelected: {
    type: Boolean,
    default: false
  }
});

// --- Emits ---
const emit = defineEmits(['select', 'edit', 'delete', 'generate', 'generate-scene-content']);

// --- Computed ---
// Sort scenes within the component
const sortedScenes = computed(() => {
  const validSceneArray = Array.isArray(props.chapter.scenes) ? props.chapter.scenes : [];
  return [...validSceneArray].sort((a, b) => (a.order_in_chapter ?? 0) - (b.order_in_chapter ?? 0));
});

// --- Methods ---
const handleSelect = () => {
  emit('select', props.chapter.id); // Emit chapter ID when header is clicked
};

const handleEdit = () => {
  emit('edit', props.chapter); // Emit the whole chapter object for editing
};

const handleDelete = () => {
  emit('delete', props.chapter.id); // Emit the whole chapter object for deletion confirmation in parent
};

const handleGenerate = () => {
  emit('generate', props.chapter.id); // Emit chapter ID for scene generation
};

const handleSceneContentGenerate = (sceneId) => {
  emit('generate-scene-content', sceneId); // Emit chapter ID for scene generation
};

</script>

<style scoped>
/* Styles are mostly moved from StructureEditor.vue's el-card section */
.chapter-item {
  border: 1px solid #e4e7ed;
  margin-bottom: 10px; /* Added margin back here */
  transition: border-color 0.3s; /* Smooth transition for active state */
}

.chapter-item.is-active {
  border-color: var(--el-color-primary);
}

.chapter-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  background-color: #f9f9f9;
  border-bottom: 1px solid transparent; /* Keep space, border shown in .chapter-scenes */
  transition: background-color 0.3s;
}

.chapter-item.is-active .chapter-header {
  background-color: #ecf5ff; /* Active header background */
}

.chapter-item:not(.is-active) .chapter-header:hover {
  background-color: #f5f7fa; /* Hover effect */
}

.chapter-title {
  flex-grow: 1;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 10px;
}

.chapter-actions {
  flex-shrink: 0;
  display: flex; /* Use flex for button alignment */
  align-items: center;
  gap: 5px; /* Space between buttons */
}

/* Reduce button padding/margin if needed */
.chapter-actions .el-button {
  padding: 4px; /* Adjust if needed */
  margin-left: 0; /* Remove default margin if using gap */
}

.chapter-scenes {
  padding: 10px 12px; /* Match header padding */
  background-color: #fff;
  border-top: 1px solid #eee; /* Separator line when expanded */
}

.scene-list-in-chapter {
  padding: 5px 0;
}

.scene-item-display {
  margin-bottom: 8px;
}

.scene-item-display:last-child {
  margin-bottom: 0;
}

.empty-scene-list {
  padding: 15px;
  text-align: center;
  background-color: #fafafa;
  border-radius: 4px;
  margin: 5px 0;
}

/* Remove styles from old ChapterItem.vue that are now handled here or unnecessary */
/* .chapter-info, .chapter-summary, .drag-handle etc. */
</style>