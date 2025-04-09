// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';

// --- Import View Components ---
// It's good practice to lazy-load routes for better performance,
// especially for views not immediately needed.
// Example: const ProjectDashboard = () => import('@/views/ProjectDashboard.vue');

// For simplicity now, we'll import directly. Replace with lazy loading as needed.
import ProjectDashboard from '@/views/ProjectDashboard.vue';
import ProjectWorkspace from '@/views/ProjectWorkspace.vue'; // Layout component

// Nested Views within ProjectWorkspace
import CharactersList from '@/views/WorldBuilding/CharactersList.vue';
import SettingsList from '@/views/WorldBuilding/SettingsList.vue';
import RelationshipsList from '@/views/WorldBuilding/RelationshipsList.vue';
import StructureEditor from '@/views/StoryStructure/StructureEditor.vue';
import SceneDetail from '@/views/SceneEditor/SceneDetail.vue'; // Handles scene metadata, content, generation trigger

import NotFound from '@/views/NotFound.vue';

const routes = [
  {
    path: '/',
    name: 'ProjectDashboard',
    component: ProjectDashboard,
    meta: { title: 'Projects' } // Optional: for setting document title
  },
  {
    // Main Workspace Layout for a specific project
    path: '/projects/:projectId',
    name: 'ProjectWorkspace',
    component: ProjectWorkspace,
    props: true, // Pass route params (projectId) as props to the component
    // Fetch project data in ProjectWorkspace's setup or beforeEnter guard
    children: [
        // Default child route for workspace (optional)
        // { path: '', name: 'ProjectOverview', component: () => import('@/views/ProjectOverview.vue') },

        // World Building Section
        {
            path: 'characters', // Relative path: /projects/:projectId/characters
            name: 'CharactersList',
            component: CharactersList,
            meta: { title: 'Characters' }
        },
        {
            path: 'settings',
            name: 'SettingsList',
            component: SettingsList,
            meta: { title: 'Settings' }
        },
        {
            path: 'relationships',
            name: 'RelationshipsList',
            component: RelationshipsList,
            meta: { title: 'Relationships' }
            // Detail/Edit for relationships might be handled within the list or a modal
        },

        // Story Structure Section
        {
            path: 'structure',
            name: 'StructureEditor',
            component: StructureEditor,
            meta: { title: 'Story Structure' }
        },

        // Scene Editor Section (Accessed perhaps from StructureEditor links)
        {
            path: 'scenes/:sceneId', // Scenes belong to a project, accessed via ID
            name: 'SceneDetail',
            component: SceneDetail,
            props: true,
            meta: { title: 'Scene Editor' }
        },
    ]
  },
  // --- Catch-all 404 Route ---
  {
    path: '/:pathMatch(.*)*', // Matches any path not caught by previous routes
    name: 'NotFound',
    component: NotFound,
    meta: { title: 'Not Found' }
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL), // Use history mode (cleaner URLs)
  routes, // Defined routes array
  // Optional: Control scroll behavior on navigation
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    } else {
      return { top: 0 };
    }
  },
});

// --- Optional: Navigation Guards ---
// Example: Set document title based on route meta
/*
router.afterEach((to) => {
  const baseTitle = 'Novel AI Writer';
  document.title = to.meta.title ? `${to.meta.title} | ${baseTitle}` : baseTitle;
});
*/

// Example: Check for authentication before accessing project workspace
/*
router.beforeEach((to, from, next) => {
  const requiresAuth = to.matched.some(record => record.name === 'ProjectWorkspace'); // Or check meta: { requiresAuth: true }
  const isAuthenticated = !!localStorage.getItem('authToken'); // Check auth status (replace with Pinia state)

  if (requiresAuth && !isAuthenticated) {
    next({ name: 'Login' }); // Redirect to login page if not authenticated
  } else {
    next(); // Proceed as normal
  }
});
*/


export default router;