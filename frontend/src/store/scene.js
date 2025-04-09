// src/store/scene.js
import {defineStore} from 'pinia';
import {sceneAPI} from '@/services/sceneAPI';       // Adjust path
import {generationAPI} from '@/services/generationAPI'; // Adjust path
import {useChapterStore} from './chapter'; // To update chapter state when scenes move

export const useSceneStore = defineStore('scene', {
    state: () => ({
        activeScene: null,      // Full details of the scene being edited/viewed
        unassignedScenes: [], // Scenes belonging to the project but not a chapter
        isLoadingDetails: false,
        isLoadingUnassigned: false,
        isGenerating: false,    // Specific loading state for RAG generation
        error: null,            // Error specific to scene operations
        generationError: null, // Error specific to RAG generation
    }),
    actions: {
        _setLoading(type, value) {
            if (type === 'details') this.isLoadingDetails = value;
            if (type === 'unassigned') this.isLoadingUnassigned = value;
            if (type === 'generating') this.isGenerating = value;
        },
        _setError(type, error) {
            const message = error ? (error.response?.data?.detail || error.message) : null;
            if (type === 'details') this.error = message;
            if (type === 'generating') this.generationError = message;
        },
        clearScenes() { // Clears both active and unassigned
            this.activeScene = null;
            this.unassignedScenes = [];
            this.isLoadingDetails = false;
            this.isLoadingUnassigned = false;
            this.isGenerating = false;
            this.error = null;
            this.generationError = null;
        },
        clearActiveScene() {
            this.activeScene = null;
            this.isLoadingDetails = false;
            this.error = null;
            // Don't clear generation error here, might be useful feedback
        },
        async fetchSceneDetails(sceneId) {
            if (!sceneId) {
                this.clearActiveScene();
                return;
            }
            // Prevent re-fetching if already active
            if (this.activeScene?.id === sceneId && !this.error) {
                this._setLoading('details', false);
                return;
            }

            this._setLoading('details', true);
            this._setError('details', null);
            this.activeScene = null;

            try {
                const response = await sceneAPI.getScene(sceneId);
                this.activeScene = response.data;
            } catch (err) {
                this._setError('details', err);
                this.activeScene = null;
            } finally {
                this._setLoading('details', false);
            }
        },
        async fetchUnassignedScenes(projectId) {
            if (!projectId) {
                this.unassignedScenes = [];
                return;
            }
            this._setLoading('unassigned', true);
            this._setError('details', null); // Use general error for list fetch
            try {
                const response = await sceneAPI.getUnassignedScenesByProject(projectId);
                this.unassignedScenes = response.data;
            } catch (err) {
                this._setError('details', err);
                this.unassignedScenes = [];
            } finally {
                this._setLoading('unassigned', false);
            }
        },
        async createScene(sceneData) {
            this._setError('details', null);
            // sceneData should include project_id, goal, and optionally chapter_id
            try {
                const response = await sceneAPI.createScene(sceneData);
                const newScene = response.data;

                // Add to the correct list (unassigned or chapter's list)
                if (newScene.chapter_id) {
                    const chapterStore = useChapterStore();
                    chapterStore.addSceneToChapter(newScene.chapter_id, newScene);
                } else {
                    this.unassignedScenes.push(newScene);
                    // sort if needed
                    this.unassignedScenes.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
                }
                return newScene;
            } catch (err) {
                this._setError('details', err);
                throw err;
            }
        },
        async updateScene(sceneId, sceneUpdateData) {
            // Decide which loading state makes sense, maybe details?
            this._setLoading('details', true);
            this._setError('details', null);
            const previousChapterId = this.activeScene?.chapter_id; // Store old chapter id
            try {
                const response = await sceneAPI.updateScene(sceneId, sceneUpdateData);
                const updatedScene = response.data;

                // Update active scene if it's the one being edited
                if (this.activeScene?.id === sceneId) {
                    this.activeScene = updatedScene;
                }

                const chapterStore = useChapterStore();
                const currentChapterId = updatedScene.chapter_id;

                // Handle changes in assignment
                if (previousChapterId && !currentChapterId) { // Moved from chapter to unassigned
                    chapterStore.removeSceneFromChapter(previousChapterId, sceneId);
                    this.unassignedScenes.push(updatedScene);
                    this.unassignedScenes.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
                } else if (!previousChapterId && currentChapterId) { // Moved from unassigned to chapter
                    this.unassignedScenes = this.unassignedScenes.filter(s => s.id !== sceneId);
                    chapterStore.addSceneToChapter(currentChapterId, updatedScene);
                } else if (previousChapterId && currentChapterId && previousChapterId !== currentChapterId) { // Moved between chapters
                    chapterStore.removeSceneFromChapter(previousChapterId, sceneId);
                    chapterStore.addSceneToChapter(currentChapterId, updatedScene);
                } else if (currentChapterId) { // Updated within the same chapter
                    // Find the chapter and update the scene within its list
                    const chapter = chapterStore.chapters.find(ch => ch.id === currentChapterId);
                    if (chapter && chapter.scenes) {
                        const sceneIndex = chapter.scenes.findIndex(s => s.id === sceneId);
                        if (sceneIndex !== -1) {
                            chapter.scenes[sceneIndex] = updatedScene;
                            // Re-sort if order changed
                            if (sceneUpdateData.order_in_chapter !== undefined) {
                                chapter.scenes.sort((a, b) => a.order_in_chapter - b.order_in_chapter);
                            }
                        }
                    }
                } else { // Updated while unassigned
                    const index = this.unassignedScenes.findIndex(s => s.id === sceneId);
                    if (index !== -1) {
                        this.unassignedScenes[index] = updatedScene;
                        this.unassignedScenes.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
                    }
                }


                return updatedScene;
            } catch (err) {
                this._setError('details', err);
                throw err;
            } finally {
                this._setLoading('details', false);
            }
        },
        async deleteScene(sceneId) {
            this._setError('details', null);
            const sceneToDelete = this.activeScene?.id === sceneId ? this.activeScene :
                this.unassignedScenes.find(s => s.id === sceneId) ||
                useChapterStore().chapters.flatMap(c => c.scenes || []).find(s => s.id === sceneId);
            const chapterId = sceneToDelete?.chapter_id;
            try {
                const response = await sceneAPI.deleteScene(sceneId);

                // Remove from active scene if it's the one deleted
                if (this.activeScene?.id === sceneId) {
                    this.activeScene = null;
                }
                // Remove from unassigned list
                this.unassignedScenes = this.unassignedScenes.filter(s => s.id !== sceneId);
                // Remove from chapter list
                if (chapterId) {
                    const chapterStore = useChapterStore();
                    chapterStore.removeSceneFromChapter(chapterId, sceneId);
                }
                return response.data;
            } catch (err) {
                this._setError('details', err);
                throw err;
            }
        },

        // --- RAG Generation ---
        async generateSceneContent(sceneId) {
            if (!sceneId) return;
            this._setLoading('generating', true);
            this._setError('generating', null);
            try {
                const response = await generationAPI.generateSceneRAG(sceneId);
                const updatedScene = response.data; // API returns the updated scene

                // Update the active scene state if it's the one being generated
                if (this.activeScene?.id === sceneId) {
                    // Merge carefully, especially if generation only returns partial data
                    // Assuming it returns the full SceneRead schema:
                    this.activeScene = updatedScene;
                }

                // Also update the scene in its respective list (chapter or unassigned)
                const chapterStore = useChapterStore();
                if (updatedScene.chapter_id) {
                    const chapter = chapterStore.chapters.find(ch => ch.id === updatedScene.chapter_id);
                    if (chapter && chapter.scenes) {
                        const sceneIndex = chapter.scenes.findIndex(s => s.id === sceneId);
                        if (sceneIndex !== -1) {
                            chapter.scenes[sceneIndex] = updatedScene; // Update scene in chapter list
                        }
                    }
                } else {
                    const index = this.unassignedScenes.findIndex(s => s.id === sceneId);
                    if (index !== -1) {
                        this.unassignedScenes[index] = updatedScene; // Update scene in unassigned list
                    }
                }

                return updatedScene;
            } catch (err) {
                this._setError('generating', err);
                // Potentially update scene status to 'generation_failed' if desired
                // if (this.activeScene?.id === sceneId) {
                //    this.activeScene.status = 'generation_failed'; // Assuming SceneStatus enum/type allows this
                // }
                throw err; // Re-throw for component feedback
            } finally {
                this._setLoading('generating', false);
            }
        }
    },
});