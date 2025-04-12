<template>
  <div class="novel-editor" :class="{ 'is-disabled': disabled }">
    <!-- Minimal Toolbar -->
    <div v-if="editor && showToolbar" class="editor-toolbar-minimal">
      <el-tooltip effect="dark" content="撤销 (Ctrl+Z)" placement="top">
        <el-button @click="editor.chain().focus().undo().run()" text bg size="small"
                   :disabled="!editor.can().undo() || disabled" aria-label="撤销">
          <el-icon><RefreshLeft /></el-icon>
        </el-button>
      </el-tooltip>
      <el-tooltip effect="dark" content="重做 (Ctrl+Y)" placement="top">
        <el-button @click="editor.chain().focus().redo().run()" text bg size="small"
                   :disabled="!editor.can().redo() || disabled" aria-label="重做">
          <el-icon><RefreshRight /></el-icon>
        </el-button>
      </el-tooltip>
      <!-- Optional Italic button -->
      <!--
      <el-tooltip effect="dark" content="斜体 (Ctrl+I)" placement="top">
         ...
      </el-tooltip>
      -->
      <!-- Character Count -->
      <span class="word-count" v-if="showWordCount && editor">
        字数: {{ characterCount }}
      </span>
    </div>

    <!-- Editor Content Area -->
    <editor-content :editor="editor" class="editor-content-area-novel"/>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, defineProps, defineEmits, computed } from 'vue';
import { Editor, EditorContent } from '@tiptap/vue-3';
// --- Core Tiptap Extensions ---
import Document from '@tiptap/extension-document';
import Paragraph from '@tiptap/extension-paragraph';
import Text from '@tiptap/extension-text';
import History from '@tiptap/extension-history'; // Undo/Redo
import Placeholder from '@tiptap/extension-placeholder'; // Placeholder text
import CharacterCount from '@tiptap/extension-character-count'; // Word/Character count
// Optional: Italic for emphasis
// import Italic from '@tiptap/extension-italic';

// --- UI Components ---
import { ElButton, ElIcon, ElTooltip } from 'element-plus';
import { RefreshLeft, RefreshRight } from '@element-plus/icons-vue';

// --- Props Definition ---
const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '从这里开始你的故事...' },
  showToolbar: { type: Boolean, default: true },
  disabled: { type: Boolean, default: false },
  showWordCount: { type: Boolean, default: true },
  // limit: { type: Number, default: null }, // Optional limit for CharacterCount
});

// --- Emits Definition ---
const emit = defineEmits(['update:modelValue', 'blur', 'focus']);

// --- Refs ---
const editor = ref(null);

// --- Helper Function: Plain Text with Newlines to HTML Paragraphs ---
// Converts a string containing newline characters (\n) into an HTML
// string where each line becomes a paragraph (<p>).
const plainTextToHtmlParagraphs = (text) => {
  if (text === null || text === undefined) return '<p></p>'; // Handle null/undefined
  // Ensure text is a string before splitting
  const textString = String(text);
  // If the input string is empty, return a single empty paragraph for Tiptap.
  if (textString.trim() === '') return '<p></p>';
  return textString
      .replace(/\n\n/g, '\n') // Normalize line endings
    .split('\n')
    // Wrap each line in <p> tags. Even empty lines become <p></p>.
    .map(line => `<p>${line}</p>`)
    .join('');
};

// --- Computed Properties ---
const characterCount = computed(() => {
  // Use .characters() method for counting characters (字数)
  return editor.value?.storage.characterCount.characters() || 0;
});

// --- Editor Setup ---
const setupEditor = () => {
  const extensions = [
    Document,
    Paragraph, // Essential for paragraphs
    Text,      // Essential for text nodes
    History.configure({ depth: 50 }), // Configure undo history size
    Placeholder.configure({
       placeholder: props.placeholder,
       emptyEditorClass: 'is-editor-empty', // Class for styling the placeholder
    }),
    // Add Italic if needed
    // Italic,
  ];

  // Add CharacterCount extension if enabled
  if (props.showWordCount) {
      extensions.push(CharacterCount.configure({
          // limit: props.limit,
          mode: 'character', // Set mode to 'character' for 字数
      }));
  }

  // Convert the initial plain text modelValue to HTML paragraphs
  const initialContent = plainTextToHtmlParagraphs(props.modelValue);

  editor.value = new Editor({
    content: initialContent, // Initialize Tiptap with the converted HTML
    editable: !props.disabled,
    extensions: extensions,
    editorProps: {
        attributes: {
            // Improve accessibility
            role: 'textbox',
            'aria-multiline': 'true',
            // You might add spellcheck="false" if you handle it elsewhere
            // spellcheck: "false",
        },
    },
    // --- Event Handlers ---
    onUpdate: () => {
      // When the editor content changes, get the text content.
      // Use blockSeparator: '\n' to ensure paragraphs are separated by a newline.
      const outputText = editor.value.getText({ blockSeparator: '\n' });

      // Only emit update if the text content has actually changed
      // compared to the current modelValue to prevent infinite loops.
      if (outputText !== props.modelValue) {
           emit('update:modelValue', outputText);
      }
    },
    onFocus: ({ event }) => emit('focus', event),
    onBlur: ({ event }) => emit('blur', event),
  });
};

// --- Watchers ---
// Watch for external changes to modelValue
watch(() => props.modelValue, (newValue) => {
  if (editor.value) {
    // Get the current editor content as plain text for comparison
    const currentEditorText = editor.value.getText({ blockSeparator: '\n' });

    // If the external value (newValue) is the same as the editor's current text,
    // do nothing to avoid unnecessary updates and cursor jumps.
    if (newValue === currentEditorText) {
      return;
    }

    // If the external value differs, convert it to HTML paragraphs
    const newHtmlValue = plainTextToHtmlParagraphs(newValue || '');

    // Use Tiptap's setContent command to update the editor.
    // The second argument 'false' prevents this action from triggering the 'onUpdate' handler again.
    // Use dangerouslyUpdateHTMLString for potentially better performance if needed, but setContent is safer.
    editor.value.commands.setContent(newHtmlValue, false);

    // Note: It's important that plainTextToHtmlParagraphs and getText({ blockSeparator: '\n' })
    // are consistent in how they handle the conversion between plain text and Tiptap's internal structure.
  }
});

// Watch for changes in the disabled state
watch(() => props.disabled, (isDisabled) => {
  editor.value?.setEditable(!isDisabled);
});

// --- Lifecycle Hooks ---
onMounted(() => {
  setupEditor();
});

onBeforeUnmount(() => {
  editor.value?.destroy();
});

</script>

<style scoped>
.novel-editor {
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  background-color: var(--el-input-bg-color, #fff);
  display: flex;
  flex-direction: column;
  transition: border-color 0.2s cubic-bezier(0.645, 0.045, 0.355, 1);
  overflow: hidden; 
}

.novel-editor.is-disabled {
  background-color: var(--el-disabled-bg-color);
  border-color: var(--el-disabled-border-color);
  cursor: not-allowed;
}

.novel-editor.is-disabled .editor-content-area-novel,
.novel-editor.is-disabled .ProseMirror {
  cursor: not-allowed;
  color: var(--el-text-color-disabled);
  -webkit-text-fill-color: var(--el-text-color-disabled); 
}

.novel-editor:focus-within {
  border-color: var(--el-color-primary);
}


.editor-toolbar-minimal {
  padding: 4px 8px;
  border-bottom: 1px solid var(--el-border-color-light);
  flex-shrink: 0;
  background-color: var(--el-bg-color-page, #f9f9f9);
  display: flex;
  align-items: center;
  gap: 6px; 
}

.word-count {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-left: auto; 
    padding: 0 5px;
    white-space: nowrap; 
    user-select: none; 
}


.editor-content-area-novel {
  flex-grow: 1; 
  padding: 20px 25px; 
  overflow-y: auto; 
  height: 400px; 
  
   min-height: 200px;
  max-height: 60vh;
}


.editor-content-area-novel > .ProseMirror {
  outline: none; 
  
  font-family: 'Source Serif 4', 'Songti SC', 'SimSun', serif;
  font-size: 16px; 
  line-height: 1.8; 
  color: var(--el-text-color-primary);
  white-space: pre-wrap; 
  word-wrap: break-word; 
  max-width: 800px;
  margin: 0 auto; 
}


.editor-content-area-novel :deep(.ProseMirror p) {
  min-height: 1.2em; 
  margin-bottom: 1.2em; 
  
  
  
  text-indent: 0;
}

.editor-content-area-novel :deep(.ProseMirror p:last-child) {
  margin-bottom: 0;
}


.editor-content-area-novel :deep(.ProseMirror p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  float: left; 
  color: var(--el-text-color-placeholder);
  pointer-events: none; 
  height: 0; 
  font-style: italic;
  
  text-indent: 0;
}


.editor-content-area-novel::-webkit-scrollbar { width: 6px; }
.editor-content-area-novel::-webkit-scrollbar-track { background: transparent; }
.editor-content-area-novel::-webkit-scrollbar-thumb { background: #ccc; border-radius: 3px; }
.editor-content-area-novel::-webkit-scrollbar-thumb:hover { background: #aaa; }
</style>