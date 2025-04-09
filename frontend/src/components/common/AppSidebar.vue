<template>
  <el-aside :width="width" class="app-sidebar">
    <el-scrollbar>
      <el-menu
        :default-active="activeRoute"
        :collapse="isCollapsed"
        :router="true"
        class="sidebar-menu"
      >
        <template v-for="item in menuItems" :key="item.path">
          <el-menu-item :index="item.path">
            <el-icon v-if="item.icon"><component :is="item.icon" /></el-icon>
            <template #title>{{ item.name }}</template>
          </el-menu-item>
        </template>
        <!-- Add more menu items or submenus as needed -->
      </el-menu>
    </el-scrollbar>
    <!-- Optional: Collapse toggle button -->
     <div class="collapse-toggle" @click="toggleCollapse" v-if="collapsible">
       <el-icon>
         <Expand v-if="isCollapsed" />
         <Fold v-else />
       </el-icon>
     </div>
  </el-aside>
</template>

<script setup>
import { ref, computed, defineProps, defineEmits } from 'vue';
import { useRoute } from 'vue-router';
import {
  ElAside,
  ElScrollbar,
  ElMenu,
  ElMenuItem,
  ElIcon,
  // Import specific icons you might use, or handle dynamically
  Fold,
  Expand,
  // Example icons (replace with actual ones needed):
  // Reading, EditPen, User, SetUp, Connection
} from '@element-plus/icons-vue'; // Import icons


// Props definition
const props = defineProps({
  menuItems: {
    type: Array,
    required: true,
    // Example structure: [{ path: '/path', name: 'Menu Name', icon: 'IconComponentName' }]
    default: () => [],
  },
  initialCollapsed: {
    type: Boolean,
    default: false,
  },
   collapsible: { // Whether the sidebar can be collapsed
    type: Boolean,
    default: true,
  },
   collapsedWidth: {
     type: String,
     default: '64px', // Standard Element Plus collapsed width
   },
   expandedWidth: {
     type: String,
     default: '200px', // Default expanded width
   }
});

// Emits definition
const emit = defineEmits(['collapse-change']);

// --- Refs ---
const isCollapsed = ref(props.initialCollapsed);
const route = useRoute();

// --- Computed ---
const activeRoute = computed(() => route.path); // Highlight based on current route

const width = computed(() => (isCollapsed.value ? props.collapsedWidth : props.expandedWidth));

// --- Methods ---
const toggleCollapse = () => {
  if (props.collapsible) {
    isCollapsed.value = !isCollapsed.value;
    emit('collapse-change', isCollapsed.value);
  }
};

</script>

<style scoped>
.app-sidebar {
  height: 100%; /* Fill parent height */
  background-color: #fff; /* Or your desired sidebar background */
  border-right: 1px solid var(--el-border-color-light);
  transition: width 0.3s ease;
  position: relative; /* Needed for absolute positioning of toggle */
  display: flex;
  flex-direction: column;
}

.el-scrollbar {
  flex-grow: 1; /* Takes up available space */
  /* Fix for potential double scrollbar issues if parent uses overflow */
  height: calc(100% - 40px); /* Adjust 40px if toggle height changes */
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 100%; /* Ensure menu fills expanded sidebar */
}
.sidebar-menu {
   border-right: none; /* Remove default border of el-menu */
}

.el-menu-item {
  /* Add custom styling for menu items if needed */
}

.el-menu-item.is-active {
  /* background-color: var(--el-color-primary-light-9); */
}

.collapse-toggle {
  height: 40px;
  line-height: 40px;
  text-align: center;
  cursor: pointer;
  border-top: 1px solid var(--el-border-color-lighter);
  color: var(--el-text-color-regular);
  background-color: #fafafa; /* Slight background difference */
}

.collapse-toggle:hover {
  background-color: #f0f0f0;
}

.collapse-toggle .el-icon {
   vertical-align: middle;
}
</style>