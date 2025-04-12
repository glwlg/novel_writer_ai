<template>
  <!-- 使用 Element Plus Collapse Item 作为卷的容器 -->
  <el-collapse-item :name="volume.id.toString()">
    <!-- 自定义 Collapse Item 的标题区域 -->
    <template #title>
      <div class="volume-header">
        <!-- 显示卷标题 -->
        <span class="volume-title">{{ volume.title || '未命名卷' }}</span>
        <!-- 卷操作按钮组 -->
        <div class="volume-actions">
          <!-- 编辑卷按钮 -->
          <el-button link type="primary" :icon="Edit" @click.stop="handleEdit" size="default" title="编辑卷信息"></el-button>
          <!-- 在本卷新建章节按钮 -->
          <el-button link type="success" :icon="Plus" @click.stop="handleCreateChapter" size="default" title="在本卷新建章节"></el-button>
          <!-- 删除卷确认提示框 -->
          <el-popconfirm
              title="确定删除此卷吗？卷下的所有章节和场景都将被删除！"
              confirm-button-text="确认删除"
              cancel-button-text="取消"
              @confirm="handleDelete"
              width="250"
          >
            <template #reference>
              <!-- 删除卷按钮触发器 -->
              <el-button link type="danger" :icon="Delete" @click.stop size="default" title="删除卷"></el-button>
            </template>
          </el-popconfirm>
        </div>
      </div>
    </template>

    <!-- 卷内容区域，包含章节列表 -->
    <!-- 如果卷下没有章节，显示空状态 -->
    <div v-if="!volume.chapters || volume.chapters.length === 0" class="empty-list inside-volume">
      <el-empty description="该卷下还没有章节" :image-size="60"></el-empty>
    </div>
    <!-- 如果有章节，显示章节列表 -->
    <div v-else class="chapter-list-in-volume">
      <!-- 遍历并渲染排序后的章节 -->
      <ChapterItem
          v-for="chapter in sortedVolumeChapters"
          :key="chapter.id"
          :chapter="chapter"
          :is-selected="selectedChapterId === chapter.id"
          @select="emitSelectChapter"
          @edit="emitEditChapter"
          @delete="emitDeleteChapter"
          @generate="emitGenerateScenes"
          @generate-scene-content="emitGenerateSceneContent"
      />
    </div>
  </el-collapse-item>
</template>

<script setup>
import { computed } from 'vue';
import { ElCollapseItem, ElButton, ElPopconfirm, ElEmpty } from 'element-plus';
import { Edit, Plus, Delete } from '@element-plus/icons-vue';
import ChapterItem from '@/components/chapter/ChapterItem.vue'; // 引入章节项组件

// --- 组件属性定义 ---
const props = defineProps({
  // 当前卷的数据对象，应包含 id, title, chapters 等
  volume: {
    type: Object,
    required: true
  },
  // 当前选中的章节ID，用于传递给 ChapterItem
  selectedChapterId: {
    type: [Number, String, null],
    default: null
  }
  // isActive 属性不再需要，el-collapse-item 的 name 属性结合父组件的 v-model 控制展开
});

// --- 组件事件定义 ---
// 定义了组件可以触发的事件
const emit = defineEmits([
  'edit',               // 请求编辑此卷
  'delete',             // 请求删除此卷
  'create-chapter',     // 请求在此卷下创建新章节
  'select-chapter',     // 转发 ChapterItem 的选择事件
  'edit-chapter',       // 转发 ChapterItem 的编辑事件
  'delete-chapter',     // 转发 ChapterItem 的删除事件
  'generate-scenes',    // 转发 ChapterItem 的生成场景事件
  'view-chapter'        // 转发 ChapterItem 的查看内容事件
]);

// --- 计算属性 ---
// 对当前卷内的章节进行排序
const sortedVolumeChapters = computed(() => {
  // 确保 props.volume.chapters 是一个数组，如果不是或为空则返回空数组
  const chaptersArray = Array.isArray(props.volume.chapters) ? props.volume.chapters : [];
  // 复制数组以避免修改原始数据，然后根据 order 字段排序
  return [...chaptersArray].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
});

// --- 方法 ---
// 处理编辑卷按钮点击事件
const handleEdit = () => {
  emit('edit', props.volume); // 触发 edit 事件，传递当前卷对象
};

// 处理删除卷确认事件
const handleDelete = () => {
  emit('delete', props.volume); // 触发 delete 事件，传递当前卷对象
};

// 处理新建章节按钮点击事件
const handleCreateChapter = () => {
  emit('create-chapter', props.volume.id); // 触发 create-chapter 事件，传递当前卷的ID
};

// --- 事件转发方法 ---
// 这些方法接收来自 ChapterItem 的事件，并将其再次触发给父组件

// 转发选择章节事件
const emitSelectChapter = (chapterId) => {
  emit('select-chapter', chapterId);
};

// 转发编辑章节事件
const emitEditChapter = (chapter) => {
  emit('edit-chapter', chapter);
};

// 转发删除章节事件
const emitDeleteChapter = (chapterId) => {
  emit('delete-chapter', chapterId);
};

// 转发生成场景事件
const emitGenerateScenes = (chapterId) => {
  emit('generate-scenes', chapterId);
};

// 转发生成场景事件
const emitGenerateSceneContent = (sceneId) => {
  emit('generate-scene-content', sceneId);
};

</script>

<style scoped>
/* 卷标题区域样式 */
.volume-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%; /* 确保占满标题栏宽度 */
}

/* 卷标题文字样式 */
.volume-title {
  font-weight: bold;
  font-size: 1.1em;
  flex-grow: 1; /* 占据多余空间 */
  margin-right: 20px; /* 与右侧按钮保持距离 */
  /* 防止标题过长时溢出 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 卷操作按钮组样式 */
.volume-actions {
  flex-shrink: 0; /* 防止按钮被压缩 */
}

/* 卷操作按钮样式 */
.volume-actions .el-button {
  margin-left: 8px; /* 按钮之间的左边距 */
}

/* 卷内章节列表区域样式 */
.chapter-list-in-volume {
  padding: 10px 15px; /* 提供章节列表的内边距 */
  background-color: #fdfdfd; /* 轻微背景色区分 */
}

/* 卷内列表为空时的提示样式 */
.empty-list.inside-volume {
  padding: 20px 0; /* 上下内边距 */
  /* text-align: center; 已由 el-empty 处理 */
}

/* 针对 el-collapse-item 内容区域的样式调整 */
:deep(.el-collapse-item__content) {
  padding-bottom: 0 !important; /* 移除 Element Plus Collapse Item 默认的底部内边距 */
}

/* 卷标题区域获得焦点时的默认轮廓可能不需要，按需保留或移除 */
/*
:deep(.el-collapse-item__header.focusing:focus:not(:hover)) {
  outline: none;
}
*/
</style>