// src/store/scene.js
import {defineStore} from 'pinia';
import {sceneAPI} from '@/services/sceneAPI';       // Adjust path
import {generationAPI} from '@/services/generationAPI'; // Adjust path
import {useChapterStore} from './chapter';

export const useSceneStore = defineStore('scene', {
    state: () => ({
        activeScene: null,      // Full details of the scene being edited/viewed
        scenes: [], // Scenes belonging to the project but not a chapter
        isLoading: false,
        isLoadingDetails: false,
        isGenerating: false,    // Specific loading state for RAG generation
        error: null,            // Error specific to scene operations
        generationError: null, // Error specific to RAG generation
    }),
    actions: {
        _setLoading(type, value) {
            if (type === 'fatch') this.isLoading = value;
            if (type === 'details') this.isLoadingDetails = value;
            if (type === 'generating') this.isGenerating = value;
        },
        _setError(type, error) {
            const message = error ? (error.response?.data?.detail || error.message) : null;
            if (type === 'details') this.error = message;
            if (type === 'generating') this.generationError = message;
        },
        clearScenes() {
            this.activeScene = null;
            this.scenes = [];
            this.isLoading = false;
            this.isLoadingDetails = false;
            this.isGenerating = false;
            this.error = null;
            this.generationError = null;
        },
        clearActiveScene() {
            this.activeScene = null;
            this.isLoadingDetails = false;
            this.error = null;
        },
        loadScenesFromChapter(chapters) {
            this.scenes = []
            for (const chapter of chapters) {
                for (const scene of chapter.scenes) {
                    this.scenes.push({...scene, chapter_id: chapter.id});
                }
            }
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
        async fetchScenes(projectId) {
            if (!projectId) {
                this.scenes = [];
                return;
            }
            this._setLoading('fatch', true);
            this._setError('details', null); // Use general error for list fetch
            try {
                const response = await sceneAPI.getScenesByProject(projectId);
                this.scenes = response.data;
            } catch (err) {
                this._setError('details', err);
                this.scenes = [];
            } finally {
                this._setLoading('fatch', false);
            }
        },
        async fetchScenesByChapter(chapterId) {
            if (!chapterId) {
                this.scenes = [];
                return;
            }
            this._setLoading('fatch', true);
            this._setError('details', null); // Use general error for list fetch
            try {
                const response = await sceneAPI.getScenesByChapter(chapterId);
                this.scenes = response.data;
            } catch (err) {
                this._setError('details', err);
                this.scenes = [];
            } finally {
                this._setLoading('fatch', false);
            }
        },
        async createScene(sceneData) {
            this._setError('details', null);
            // sceneData should include project_id, goal, and optionally chapter_id
            try {
                const response = await sceneAPI.createScene(sceneData);
                const newScene = response.data;

                if (newScene.chapter_id) {
                    const chapterStore = useChapterStore();
                    chapterStore.addSceneToChapter(newScene.chapter_id, newScene);
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
            try {
                const response = await sceneAPI.updateScene(sceneId, sceneUpdateData);
                const index = this.scenes.findIndex(s => s.id === sceneId);
                const updatedScene = response.data;

                if (index!== -1) {
                    this.scenes[index] = updatedScene;
                }

                // Update active scene if it's the one being edited
                if (this.activeScene?.id === sceneId) {
                    this.activeScene = updatedScene;
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
            try {
                const response = await sceneAPI.deleteScene(sceneId);
                const sceneToDelete = response.data;
                const chapterId = sceneToDelete?.chapter_id;

                if (this.activeScene?.id === sceneId) {
                    this.activeScene = null;
                }
                console.log("scenes=====",this.scenes);
                // Remove from scenes list
                this.scenes = this.scenes.filter(s => s.id !== sceneId);
                console.log("scenes=====",this.scenes);

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

                const chapterStore = useChapterStore();
                if (updatedScene.chapter_id) {
                    const chapter = chapterStore.chapters.find(ch => ch.id === updatedScene.chapter_id);
                    if (chapter && chapter.scenes) {
                        const sceneIndex = chapter.scenes.findIndex(s => s.id === sceneId);
                        if (sceneIndex !== -1) {
                            chapter.scenes[sceneIndex] = updatedScene; // Update scene in chapter list
                        }
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