// src/store/project.js
import {defineStore} from 'pinia';
import {projectAPI} from '@/services/projectAPI'; // Adjust path as needed
import {useCharacterStore} from './character';
import {useSettingStore} from './setting';
import {useRelationshipStore} from './relationship';
import {useChapterStore} from './chapter';
import {useSceneStore} from './scene';
import {useVolumeStore} from "@/store/volume.js";

export const useProjectStore = defineStore('project', {
    state: () => ({
        activeProject: null,
        projectsList: [],
        currentProject: null, // Holds the full details of the currently selected project
        isLoadingList: false,
        isLoadingDetails: false,
        error: null,
    }),
    getters: {
        hasActiveProject: (state) => !!state.currentProject,
    },
    actions: {
        _setLoading(type, value) {
            if (type === 'list') this.isLoadingList = value;
            if (type === 'details') this.isLoadingDetails = value;
        },
        _setError(error) {
            this.error = error ? (error.response?.data?.detail || error.message || 'An unknown error occurred') : null;
            // Optionally push to global UI store as well
            // const uiStore = useUIStore();
            // if (error) uiStore.setError(this.error); else uiStore.clearError();
        },
        async fetchProjects() {
            this._setLoading('list', true);
            this._setError(null);
            try {
                const response = await projectAPI.getProjects(); // Assuming limit/skip handled or defaulted
                this.projectsList = response.data;
            } catch (err) {
                this._setError(err);
            } finally {
                this._setLoading('list', false);
            }
        },
        async fetchProjectDetails(projectId) {
            if (!projectId) {
                this.currentProject = null;
                return;
            }
            // Prevent re-fetching if already current
            if (this.currentProject?.id === projectId && !this.error) {
                this._setLoading('details', false); // Ensure loading is false if cached
                return;
            }

            this._setLoading('details', true);
            this._setError(null);
            this.currentProject = null; // Clear previous project first

            try {
                const response = await projectAPI.getProject(projectId);
                this.currentProject = response.data;

            } catch (err) {
                this._setError(err);
                this.currentProject = null; // Ensure project is null on error
            } finally {
                this._setLoading('details', false);
            }
        },
        async createProject(projectData) {
            // No loading state change here, handled by component potentially
            this._setError(null);
            try {
                const response = await projectAPI.createProject(projectData);
                this.projectsList.push(response.data); // Add to the list
                return response.data; // Return the created project
            } catch (err) {
                this._setError(err);
                throw err; // Re-throw for component-level handling (e.g., form validation)
            }
        },
        async updateProject(projectId, projectUpdateData) {
            this._setLoading('details', true); // Use details loading as it affects the current project view
            this._setError(null);
            try {
                const response = await projectAPI.updateProject(projectId, projectUpdateData);
                // Update the list
                const index = this.projectsList.findIndex(p => p.id === projectId);
                if (index !== -1) {
                    this.projectsList[index] = {...this.projectsList[index], ...response.data};
                }
                // Update current project if it's the one being edited
                if (this.currentProject?.id === projectId) {
                    this.currentProject = {...this.currentProject, ...response.data};
                }
                return response.data;
            } catch (err) {
                this._setError(err);
                throw err;
            } finally {
                this._setLoading('details', false);
            }
        },
        async deleteProject(projectId) {
            this._setError(null);
            // Optional: Add a specific loading state for deletion
            try {
                const response = await projectAPI.deleteProject(projectId);
                this.projectsList = this.projectsList.filter(p => p.id !== projectId);

                // If the deleted project was the current one, clear it
                if (this.currentProject?.id === projectId) {

                    this.currentProject = null;
                    // Clear related stores as well
                    useCharacterStore().clearCharacters();
                    useSettingStore().clearSettings();
                    useRelationshipStore().clearRelationships();
                    useChapterStore().clearChapters();
                    useSceneStore().clearScenes();
                }
                return response.data;
            } catch (err) {
                this._setError(err);
                throw err;
            }
        },
        // Action to clear project details when navigating away or logging out
        clearCurrentProject() {
            this.currentProject = null;
            this.error = null;
            // Clear related stores
            useCharacterStore().clearCharacters();
            useSettingStore().clearSettings();
            useRelationshipStore().clearRelationships();
            useChapterStore().clearChapters();
            useSceneStore().clearScenes();
        }
    },
});