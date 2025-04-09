<template>
  <el-dialog
    :model-value="visible"
    :title="isEditMode ? '编辑人物关系' : '创建人物关系'"
    width="600px"
    @close="closeDialog"
    :close-on-click-modal="false"
    append-to-body
    destroy-on-close
  >
    <el-form
      ref="relationshipFormRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      v-loading="loading"
    >
      <el-form-item label="角色一" prop="character1_id">
        <el-select
          v-model="formData.character1_id"
          placeholder="请选择第一个角色"
          filterable
          style="width: 100%;"
          :disabled="isEditMode"
        >
          <el-option
            v-for="char in availableCharactersForSelect1"
            :key="char.id"
            :label="char.name"
            :value="char.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="角色二" prop="character2_id">
        <el-select
          v-model="formData.character2_id"
          placeholder="请选择第二个角色"
          filterable
          style="width: 100%;"
          :disabled="isEditMode"
        >
          <el-option
            v-for="char in availableCharactersForSelect2"
            :key="char.id"
            :label="char.name"
            :value="char.id"
          />
        </el-select>
         <div v-if="charactersAreSame" class="el-form-item__error" style="color: var(--el-color-danger); font-size: 12px; line-height: 1; padding-top: 4px;">
           角色一和角色二不能是同一个人。
         </div>
      </el-form-item>

      <el-form-item label="关系类型" prop="relationship_type">
        <el-select v-model="formData.relationship_type" placeholder="请选择关系类型" style="width: 100%;">
          <el-option
            v-for="(item, key) in RELATIONSHIP_TYPE_MAP"
            :key="key"
            :label="item.text"
            :value="key"
          />
           <!-- 可以添加一个“其他”选项，或者允许用户自定义 -->
        </el-select>
      </el-form-item>

      <el-form-item label="关系描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="（可选）详细描述这两个角色之间的关系"
        />
      </el-form-item>

    </el-form>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="closeDialog">取 消</el-button>
        <el-button type="primary" @click="submitForm" :loading="loading" :disabled="charactersAreSame">
          {{ isEditMode ? '保 存' : '创 建' }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch, computed, nextTick } from 'vue';
import {
    ElDialog, ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElButton, ElMessage, ElLoading
} from 'element-plus';
import { useCharacterStore } from '@/store/character'; // 调整路径
import { useRelationshipStore } from '@/store/relationship'; // 调整路径

// --- Props ---
const props = defineProps({
  visible: { // 控制对话框显示/隐藏
    type: Boolean,
    required: true,
  },
  initialData: { // 编辑时传入的初始数据
    type: Object,
    default: null,
  },
  projectId: { // 当前项目ID
    type: [String, Number],
    required: true,
  },
  characters: { // 当前项目的所有角色列表
      type: Array,
      required: true,
      default: () => []
  }
});

// --- Emits ---
const emit = defineEmits(['update:visible', 'success']);

// --- Stores ---
const relationshipStore = useRelationshipStore();
// const characterStore = useCharacterStore(); // 通过 props 传入了 characters

// --- Refs ---
const relationshipFormRef = ref(null);
const loading = ref(false); // 表单提交时的加载状态

// --- Constants ---
// 关系类型定义 (与 RelationshipDisplay.vue 保持一致或共享)
const RELATIONSHIP_TYPE_MAP = {
  'Friend': { text: '朋友' },
  'Enemy': { text: '敌人' },
  'Family': { text: '家人' },
  'Romantic': { text: '恋人' },
  'Ally': { text: '盟友' },
  'Rival': { text: '对手' },
};

// --- Reactive Data ---
const formData = reactive({
  character1_id: null,
  character2_id: null,
  relationship_type: '',
  description: '',
});

// --- Computed ---
const isEditMode = computed(() => !!props.initialData?.id);

// 过滤下拉选项，防止选择同一个角色
const availableCharactersForSelect1 = computed(() => {
    // 简单返回所有角色，因为编辑时禁用
    return props.characters;
});
const availableCharactersForSelect2 = computed(() => {
     // 简单返回所有角色，因为编辑时禁用
    return props.characters;
});

// 检查两个角色是否相同
const charactersAreSame = computed(() => {
    return formData.character1_id !== null && formData.character2_id !== null && formData.character1_id === formData.character2_id;
});

// --- Form Rules ---
const validateCharactersDifferent = (rule, value, callback) => {
    if (formData.character1_id && formData.character2_id && formData.character1_id === formData.character2_id) {
        callback(new Error('角色一和角色二不能是同一个人'));
    } else {
        callback();
    }
};

const formRules = reactive({
  character1_id: [
    { required: true, message: '请选择第一个角色', trigger: 'change' },
    { validator: validateCharactersDifferent, trigger: 'change' } // 验证是否相同
  ],
  character2_id: [
    { required: true, message: '请选择第二个角色', trigger: 'change' },
    { validator: validateCharactersDifferent, trigger: 'change' } // 验证是否相同
  ],
  relationship_type: [
    { required: true, message: '请选择关系类型', trigger: 'change' },
  ],
  description: [
    // 可选，无规则
  ],
});


// --- Watchers ---
watch(() => props.visible, (newVal) => {
  if (newVal) {
    // 对话框打开时，重置表单并填充初始数据（如果是编辑模式）
    nextTick(() => { // 确保 DOM 更新后再访问 ref
        relationshipFormRef.value?.resetFields(); // 清除之前的校验状态和值
        if (isEditMode.value && props.initialData) {
            Object.assign(formData, {
                character1_id: props.initialData.character1_id,
                character2_id: props.initialData.character2_id,
                relationship_type: props.initialData.relationship_type,
                description: props.initialData.description || '',
            });
        } else {
             // 重置为默认空状态
            Object.assign(formData, {
                character1_id: null,
                character2_id: null,
                relationship_type: '',
                description: '',
            });
        }
    });
  }
});

// --- Methods ---
const closeDialog = () => {
  emit('update:visible', false);
};

const submitForm = async () => {
  if (!relationshipFormRef.value) return;

  try {
    await relationshipFormRef.value.validate(); // 触发表单校验
    if (charactersAreSame.value) {
        ElMessage.error('角色一和角色二不能是同一个人。');
        return;
    }
    loading.value = true;

    if (isEditMode.value) {
      // 编辑模式：调用更新接口
      const updateData = {
        relationship_type: formData.relationship_type,
        description: formData.description,
      };
      await relationshipStore.updateRelationship(props.initialData.id, updateData);
      ElMessage.success('人物关系更新成功！');
    } else {
      // 创建模式：调用创建接口
      const createData = {
        character1_id: formData.character1_id,
        character2_id: formData.character2_id,
        relationship_type: formData.relationship_type,
        description: formData.description,
        // project_id 由 store action 或 API service 添加
      };
      await relationshipStore.createRelationship(Number(props.projectId), createData);
      ElMessage.success('人物关系创建成功！');
    }
    emit('success'); // 通知父组件操作成功
    closeDialog();    // 关闭对话框

  } catch (validationError) {
    if (validationError === false) { // validate() 返回 false 表示校验失败
        console.log('表单校验失败');
    } else { // API 调用或其他错误
        console.error('提交关系时出错:', validationError);
        // 错误消息已由 store 的 _setError 处理，这里可以不显示 ElMessage
        // ElMessage.error(relationshipStore.error || '操作失败，请稍后重试');
    }
  } finally {
    loading.value = false;
  }
};

</script>

<style scoped>
.dialog-footer {
  text-align: right;
}
</style>